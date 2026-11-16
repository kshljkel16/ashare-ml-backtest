"""Step 6 — Download company announcements (公告) for CSI 300 stocks (provided).

    python -m qml.announcements --start 20240101 --end 20241231

Source: East Money's announcement API — the same endpoint AkShare's `stock_notice_report`
uses — queried per stock, so ~300 small requests instead of thousands of market-wide pages.
One CSV per stock in data/raw_notices/<year range>/ (an interrupted download resumes), then
combined into data/announcements_<start>_<end>.csv with columns:

    code, date, title, category

`date` is the announcement DATE only. The time of day is not reliable in this source, so
Step 6 aligns announcements conservatively: an announcement dated D is assumed to be
tradable only at the first open AFTER the close of D (GUIDE.md, Step 6).
"""

from __future__ import annotations

import argparse
import math
import time
from pathlib import Path

import pandas as pd

API = "https://np-anotice-stock.eastmoney.com/api/security/ann"


def _parse_page(items: list[dict], code: str) -> list[dict]:
    rows = []
    for it in items:
        columns = it.get("columns") or [{}]
        rows.append({
            "code": code,
            "date": str(it.get("notice_date", ""))[:10],
            "title": (it.get("title") or "").strip(),
            "category": columns[0].get("column_name", ""),
        })
    return rows


def fetch_stock(code: str, start: str, end: str, session=None) -> pd.DataFrame:
    """All announcements of one stock between start and end (YYYYMMDD)."""
    import requests

    s = session or requests.Session()
    params = {"sr": "-1", "page_size": "100", "page_index": "1", "ann_type": "A",
              "client_source": "web", "f_node": "0", "s_node": "0", "stock_list": code,
              "begin_time": f"{start[:4]}-{start[4:6]}-{start[6:]}",
              "end_time": f"{end[:4]}-{end[4:6]}-{end[6:]}"}
    first = s.get(API, params=params, timeout=20).json()["data"]
    rows = _parse_page(first.get("list") or [], code)
    for page in range(2, math.ceil(first.get("total_hits", 0) / 100) + 1):
        params["page_index"] = str(page)
        data = s.get(API, params=params, timeout=20).json()["data"]
        rows += _parse_page(data.get("list") or [], code)
        time.sleep(0.2)
    return pd.DataFrame(rows, columns=["code", "date", "title", "category"])


def download(codes: list[str], start: str, end: str) -> pd.DataFrame:
    import requests

    raw_dir = Path("data/raw_notices") / f"{start}_{end}"
    raw_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers["User-Agent"] = "Mozilla/5.0"
    for i, code in enumerate(codes, 1):
        path = raw_dir / f"{code}.csv"
        if path.exists():
            continue
        for attempt in range(3):
            try:
                fetch_stock(code, start, end, session).to_csv(path, index=False)
                break
            except Exception as e:
                print(f"  {code}: attempt {attempt + 1} failed ({e})")
                time.sleep(2 ** attempt)
        if i % 25 == 0:
            print(f"  {i}/{len(codes)} stocks")
        time.sleep(0.3)

    frames = [pd.read_csv(p, dtype={"code": str}) for p in sorted(raw_dir.glob("*.csv"))]
    df = pd.concat(frames, ignore_index=True).dropna(subset=["title"])
    df = df[df["title"].str.len() > 0].drop_duplicates(["code", "date", "title"])
    out = Path(f"data/announcements_{start}_{end}.csv")
    df.to_csv(out, index=False)
    return df


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="20240101")
    ap.add_argument("--end", default="20241231")
    args = ap.parse_args()
    codes = sorted(pd.read_csv("data/prices.csv", dtype={"code": str}, usecols=["code"])["code"]
                   .str.zfill(6).unique())
    print(f"{len(codes)} stocks; downloading announcements {args.start} -> {args.end} ...")
    df = download(codes, args.start, args.end)
    print(f"wrote {len(df):,} announcements for {df.code.nunique()} stocks")


if __name__ == "__main__":
    main()
