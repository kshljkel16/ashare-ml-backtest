"""Step 6 — Event study: do announcements classified by an LLM predict what happens next?

    python -m qml.event_study --start 20240101 --end 20241231            # cost estimate only
    python -m qml.event_study --start 20240101 --end 20241231 --sample 200 --yes   # small dry run
    python -m qml.event_study --start 20240101 --end 20241231 --yes      # full run

Needs data/prices.csv (Step 1), data/announcements_<start>_<end>.csv (python -m qml.announcements)
and your Moonshot key in .env. Labels are cached in .cache/notice_labels.json, so a rerun or a
larger run never pays twice for the same title.

Writes reports/event_study_<start>_<end>/: results.md, a chart, every labelled announcement,
and label_check.csv — 50 random titles for YOU to label by hand (GUIDE.md, Step 6).
"""

from __future__ import annotations

import argparse
import math
import os
from pathlib import Path

import numpy as np
import pandas as pd

from qml.dataset import clean_panel
from qml.events import abnormal_returns, align_to_trading_days, daily_event_scores, event_study
from qml.llm import MoonshotClient, TitleClassifier

HORIZONS = [1, 5, 20]
BATCH = 25


def estimate_cost(n_titles: int, price_in: float, price_out: float) -> float:
    """Rough upper estimate: ~650 prompt tokens per batch + ~40 per title in, ~20 per title out."""
    batches = math.ceil(n_titles / BATCH)
    tokens_in = batches * 650 + n_titles * 40
    tokens_out = n_titles * 20
    return (tokens_in * price_in + tokens_out * price_out) / 1e6


def chart(out: Path, table: pd.DataFrame) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    groups = [g for g in ["negative", "neutral", "no_news", "positive"] if g in set(table.group)]
    colors = {"negative": "#c0504d", "neutral": "#999999", "no_news": "#cccccc", "positive": "#2f6fde"}
    fig, ax = plt.subplots(figsize=(8, 4))
    width = 0.8 / len(groups)
    for k, g in enumerate(groups):
        sub = table[table.group == g].set_index("horizon").reindex(HORIZONS)
        ax.bar([i + (k - (len(groups) - 1) / 2) * width for i in range(len(HORIZONS))],
               sub["mean"] * 1e4, width, label=g, color=colors[g])
    ax.set_xticks(range(len(HORIZONS)), [f"{h} day{'s' if h > 1 else ''}" for h in HORIZONS])
    ax.set_ylabel("mean abnormal return (bp)")
    ax.set_title("Return vs other stocks after an announcement (from the next open)")
    ax.axhline(0, color="#555555", linewidth=0.8)
    ax.grid(alpha=0.3, axis="y")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "event_study.png", dpi=150)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="20240101")
    ap.add_argument("--end", default="20241231")
    ap.add_argument("--sample", type=int, default=0, help="classify only N random titles (dry run)")
    ap.add_argument("--yes", action="store_true", help="actually call the LLM")
    args = ap.parse_args()

    from dotenv import load_dotenv
    load_dotenv()
    price_in = float(os.getenv("LLM_PRICE_INPUT_PER_MTOK") or 0)
    price_out = float(os.getenv("LLM_PRICE_OUTPUT_PER_MTOK") or 0)

    ann_path = Path(f"data/announcements_{args.start}_{args.end}.csv")
    if not ann_path.exists():
        raise SystemExit(f"{ann_path} not found — run: python -m qml.announcements "
                         f"--start {args.start} --end {args.end}")
    ann = pd.read_csv(ann_path, dtype={"code": str})
    ann["code"] = ann["code"].str.zfill(6)
    if args.sample:
        ann = ann.sample(n=min(args.sample, len(ann)), random_state=0)
    titles = sorted(ann["title"].unique())

    est = estimate_cost(len(titles), price_in, price_out)
    print(f"{len(ann):,} announcements, {len(titles):,} unique titles, "
          f"{ann.code.nunique()} stocks. Estimated LLM cost: about ${est:.2f} "
          f"(fewer if some titles are already cached).")
    if not args.yes:
        print("Nothing sent to the LLM. Add --yes to run (try --sample 200 first).")
        return

    clf = TitleClassifier(MoonshotClient(), batch_size=BATCH, price_in=price_in,
                          price_out=price_out, cache_path=Path(".cache/notice_labels.json"))
    labels = dict(zip(titles, clf.classify(titles)))
    ann["sentiment"] = ann["title"].map(lambda t: labels[t].sentiment)
    ann["event"] = ann["title"].map(lambda t: labels[t].event)
    spent = sum(l.cost_usd for l in labels.values())
    print(f"LLM: {clf.calls} calls, ${spent:.4f}; unparsed titles: "
          f"{sum(l.sentiment is None for l in labels.values())}")

    prices = clean_panel(pd.read_csv("data/prices.csv", dtype={"code": str}))
    aligned = align_to_trading_days(ann, prices["date"])
    events = daily_event_scores(aligned)
    abn = abnormal_returns(prices, HORIZONS)
    start, end = pd.Timestamp(args.start), pd.Timestamp(args.end)
    abn = abn[(abn.date >= start) & (abn.date <= end)]
    table = event_study(abn, events, HORIZONS)

    # Which event types move prices? (5-day abnormal return after each non-routine announcement)
    per_ann = aligned.dropna(subset=["sentiment"]).merge(
        abn[["code", "date", "abn_5"]], left_on=["code", "signal_date"], right_on=["code", "date"],
        suffixes=("", "_px"))
    by_event = (per_ann.groupby(["event", "sentiment"])["abn_5"]
                .agg(n="count", mean="mean").reset_index().sort_values("n", ascending=False))

    out = Path("reports") / f"event_study_{args.start}_{args.end}" if not args.sample else \
        Path("reports") / f"event_study_{args.start}_{args.end}_sample{args.sample}"
    out.mkdir(parents=True, exist_ok=True)
    aligned.to_csv(out / "labelled_announcements.csv", index=False)
    check = aligned.dropna(subset=["sentiment"]).sample(n=min(50, len(aligned)), random_state=1)
    check = check[["code", "date", "title", "sentiment", "event"]].rename(
        columns={"sentiment": "llm_sentiment", "event": "llm_event"})
    check["my_sentiment"] = ""
    check.to_csv(out / "label_check.csv", index=False, encoding="utf-8-sig")
    chart(out, table)

    dist = aligned["sentiment"].value_counts(dropna=False).rename("count").to_frame()
    wide = table.pivot(index="group", columns="horizon", values=["mean", "t_stat", "n"])
    lines = [
        f"# Event study {args.start}–{args.end}",
        "",
        f"{len(ann):,} announcements ({len(titles):,} unique titles), labelled by Kimi for ${spent:.2f}.",
        "Abnormal return = stock's return minus the equal-weight average of all stocks, from the open",
        "after the announcement's trading day (the first price you could actually trade at).",
        "",
        "## Sentiment distribution", "", dist.to_markdown(), "",
        "## Abnormal returns by group (mean in %, t-stat, number of stock-days)", "",
        (wide["mean"] * 100).round(3).add_prefix("mean_%_h").join(
            wide["t_stat"].round(2).add_prefix("t_h")).join(wide["n"].add_prefix("n_h")).to_markdown(),
        "",
        "## 5-day abnormal return by event type and sentiment", "",
        by_event.assign(mean=lambda d: (d["mean"] * 100).round(3)).rename(
            columns={"mean": "mean_%"}).to_markdown(index=False),
        "",
        "![event study](event_study.png)",
    ]
    (out / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("\n" + (wide["mean"] * 100).round(3).to_string())
    print("\nt-stats:\n" + wide["t_stat"].round(2).to_string())
    print(f"\nWrote {out}/results.md, event_study.png, labelled_announcements.csv, label_check.csv")


if __name__ == "__main__":
    main()
