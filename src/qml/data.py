"""Download CSI 300 daily data with AkShare (provided — read it, you don't need to write it).

    python -m qml.data --start 20180101 --end 20251231

Writes one CSV per stock to data/raw/ (so an interrupted download resumes where it
stopped), then combines them into data/prices.csv with the project's English columns:
    date, code, open, high, low, close, volume, amount, turnover

Notes you should be able to explain (GUIDE.md, Step 1):
  * Prices are 后复权 (hfq, backward-adjusted): splits and dividends are folded into the
    price history, so returns computed from it are real returns. Unadjusted prices show
    fake -50% "crashes" on split days.
  * The stock list is TODAY's CSI 300. Stocks that were in the index in 2018 but have
    since been removed (often because they did badly) are missing. That is
    SURVIVORSHIP BIAS, and it makes any backtest look better than reality.
  * AkShare scrapes public websites, so function names and columns occasionally change.
    If a call fails, check the AkShare docs for the current name: the rest of the
    project only depends on the 9 English columns above.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import pandas as pd

RAW_DIR = Path("data/raw")
OUT_PATH = Path("data/prices.csv")

# AkShare's Chinese column names -> our English names
COLUMNS = {
    "日期": "date", "开盘": "open", "最高": "high", "最低": "low", "收盘": "close",
    "成交量": "volume", "成交额": "amount", "换手率": "turnover",
}


def csi300_codes() -> list[str]:
    """Current CSI 300 constituents as 6-digit codes (see the survivorship note above)."""
    import akshare as ak

    df = ak.index_stock_cons_csindex(symbol="000300")
    col = next(c for c in df.columns if "代码" in c and "指数" not in c)
    return sorted(df[col].astype(str).str.zfill(6).unique())


def download_one(code: str, start: str, end: str) -> pd.DataFrame:
    import akshare as ak

    df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start,
                            end_date=end, adjust="hfq")
    df = df.rename(columns=COLUMNS)[list(COLUMNS.values())]
    df.insert(1, "code", code)
    return df


def download_all(codes: list[str], start: str, end: str, pause_s: float = 0.3) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for i, code in enumerate(codes, 1):
        path = RAW_DIR / f"{code}.csv"
        if path.exists():
            continue                                    # already downloaded: resume
        for attempt in range(3):
            try:
                download_one(code, start, end).to_csv(path, index=False)
                break
            except Exception as e:                      # network blip: wait and retry
                print(f"  {code}: attempt {attempt + 1} failed ({e})")
                time.sleep(2 ** attempt)
        if i % 25 == 0:
            print(f"  {i}/{len(codes)} stocks downloaded")
        time.sleep(pause_s)                             # be polite to the data source


def combine() -> pd.DataFrame:
    frames = [pd.read_csv(p, dtype={"code": str}) for p in sorted(RAW_DIR.glob("*.csv"))]
    df = pd.concat(frames, ignore_index=True)
    df.to_csv(OUT_PATH, index=False)
    return df


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="20180101")
    ap.add_argument("--end", default="20251231")
    args = ap.parse_args()

    codes = csi300_codes()
    print(f"{len(codes)} CSI 300 stocks; downloading {args.start} -> {args.end} ...")
    download_all(codes, args.start, args.end)
    df = combine()
    print(f"wrote {len(df):,} rows, {df.code.nunique()} stocks -> {OUT_PATH}")


if __name__ == "__main__":
    main()
