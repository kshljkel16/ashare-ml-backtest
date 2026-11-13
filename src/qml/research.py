"""Step 5 — The full research run (provided: orchestration and plots; it uses YOUR functions).

    python -m qml.research --synthetic     # planted-signal data: checks the pipeline end to end
    python -m qml.research                 # real CSI 300 data from data/prices.csv

Writes reports/<name>/results.md and three charts.

The comparison is fair by construction: the baseline (momentum) and the model are
evaluated on EXACTLY the same out-of-sample dates — the dates the walk-forward produced
predictions for. Comparing a model's out-of-sample period with a baseline measured over
the whole history would be comparing different markets.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from qml.config import COST_ONE_WAY, FEATURES, HORIZON, N_QUANTILES
from qml.dataset import add_forward_return, clean_panel
from qml.features import compute_features, rank_by_date
from qml.metrics import ic_summary, rank_ic_by_date
from qml.portfolio import (annualised_return, max_drawdown, net_of_costs,
                           quantile_returns, sharpe, top_quantile_turnover)
from qml.walkforward import make_splits, walk_forward_predict

PERIODS_PER_YEAR = 250 / HORIZON
COST_LEVELS = [0.0, 0.0005, COST_ONE_WAY, 0.003]      # 0, 5, 15, 30 bp one way


def load(synthetic: bool) -> pd.DataFrame:
    if synthetic:
        from qml.synthetic import make_panel
        return make_panel()
    return pd.read_csv("data/prices.csv", dtype={"code": str})


def evaluate_signal(df: pd.DataFrame, signal: str) -> dict:
    """IC and portfolio statistics for one signal column."""
    ic = rank_ic_by_date(df, signal)
    q = quantile_returns(df, signal)
    turnover = top_quantile_turnover(df, signal)
    top, bottom, universe = q[f"Q{N_QUANTILES}"], q["Q1"], q.mean(axis=1)

    long_short = top - bottom                                   # theoretical: A-share shorting is limited
    long_excess = net_of_costs(top, turnover, COST_ONE_WAY) - universe   # realistic: long-only vs equal-weight
    row = {f"ic_{k}": v for k, v in ic_summary(ic).items()}
    row.update({
        "ls_ann_return": annualised_return(long_short, PERIODS_PER_YEAR),
        "ls_sharpe": sharpe(long_short, PERIODS_PER_YEAR),
        "ls_max_dd": max_drawdown(long_short),
        "long_excess_ann_net": annualised_return(long_excess, PERIODS_PER_YEAR),
        "long_excess_sharpe_net": sharpe(long_excess, PERIODS_PER_YEAR),
        "turnover": float(turnover.iloc[1:].mean()) if len(turnover) > 1 else 1.0,
    })
    for c in COST_LEVELS:
        net = net_of_costs(top, turnover, c) - universe
        row[f"long_excess_sharpe_{int(c * 1e4)}bp"] = sharpe(net, PERIODS_PER_YEAR)
    return {"row": row, "ic": ic, "q": q, "long_short": long_short, "long_excess": long_excess}


def plots(out: Path, results: dict[str, dict]) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colors = {"model": "#2f6fde", "baseline_mom_20": "#999999"}

    fig, ax = plt.subplots(figsize=(8, 4))
    for name, r in results.items():
        r["ic"].cumsum().plot(ax=ax, label=name, color=colors.get(name, "#bbbbbb"))
    ax.set_title("Cumulative RankIC (out-of-sample)")
    ax.set_ylabel("sum of daily RankIC")
    ax.grid(alpha=0.3); ax.legend()
    fig.tight_layout(); fig.savefig(out / "ic_cumulative.png", dpi=150); plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4))
    width = 0.38
    for k, (name, r) in enumerate(results.items()):
        m = r["q"].mean() * PERIODS_PER_YEAR
        ax.bar([i + (k - 0.5) * width for i in range(len(m))], m.values, width,
               label=name, color=colors.get(name, "#bbbbbb"))
    ax.set_xticks(range(N_QUANTILES), [f"Q{i + 1}" for i in range(N_QUANTILES)])
    ax.set_title("Annualised return by signal quintile (gross)")
    ax.axhline(0, color="#555555", linewidth=0.8)
    ax.grid(alpha=0.3, axis="y"); ax.legend()
    fig.tight_layout(); fig.savefig(out / "quantile_returns.png", dpi=150); plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4))
    for name, r in results.items():
        (1 + r["long_excess"].fillna(0)).cumprod().plot(ax=ax, label=f"{name} (long-only excess, net)",
                                                        color=colors.get(name, "#bbbbbb"))
    ax.axhline(1, color="#555555", linewidth=0.8)
    ax.set_title(f"Top quintile vs equal-weight universe, after {COST_ONE_WAY * 1e4:.0f} bp costs")
    ax.grid(alpha=0.3); ax.legend()
    fig.tight_layout(); fig.savefig(out / "equity_curve.png", dpi=150); plt.close(fig)


def write_results(out: Path, results: dict[str, dict], n_splits: int, oos: tuple) -> None:
    table = pd.DataFrame({name: r["row"] for name, r in results.items()}).T
    lines = [
        f"# Results — out-of-sample {oos[0]:%Y-%m-%d} to {oos[1]:%Y-%m-%d}",
        "",
        f"Walk-forward: {n_splits} retrains. Horizon {HORIZON} days, rebalanced every {HORIZON} days, "
        f"{N_QUANTILES} quantiles. Baseline and model are measured on the same dates.",
        "",
        table.round(4).to_markdown(),
        "",
        "- `ls_*`: top minus bottom quintile, gross (a measure of signal quality; shorting A-shares is restricted).",
        f"- `long_excess_*`: top quintile minus the equal-weight universe, after costs "
        f"({COST_ONE_WAY * 1e4:.0f} bp one way unless named). This is the tradable version.",
        "- `ic_t_stat` ignores the overlap of 5-day labels on consecutive days, so it overstates significance.",
        "",
        "![cumulative IC](ic_cumulative.png)",
        "",
        "![quintile returns](quantile_returns.png)",
        "",
        "![equity curve](equity_curve.png)",
    ]
    (out / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--synthetic", action="store_true", help="use planted-signal data")
    args = ap.parse_args()
    name = "synthetic" if args.synthetic else "csi300"
    out = Path("reports") / (name if HORIZON == 5 else f"{name}_h{HORIZON}")
    out.mkdir(parents=True, exist_ok=True)

    print("Steps 1-2: clean, label, features ...")
    df = compute_features(add_forward_return(clean_panel(load(args.synthetic)), HORIZON))
    ranked = rank_by_date(df, FEATURES)

    print("Step 4: walk-forward model ...")
    splits = make_splits(ranked["date"])
    preds = walk_forward_predict(ranked, FEATURES, splits)
    oos = ranked.merge(preds, on=["date", "code"], how="inner")    # out-of-sample rows only

    print("Steps 3+5: evaluate baseline and model on the same dates ...")
    results = {"baseline_mom_20": evaluate_signal(oos, "mom_20"),
               "model": evaluate_signal(oos, "pred")}
    plots(out, results)
    write_results(out, results, len(splits), (oos["date"].min(), oos["date"].max()))

    table = pd.DataFrame({k: r["row"] for k, r in results.items()}).T
    cols = ["ic_mean", "ic_icir", "ls_sharpe", "long_excess_ann_net", "long_excess_sharpe_net", "turnover"]
    print("\n" + table[cols].round(4).to_string())
    print(f"\nWrote {out}/results.md and 3 charts")


if __name__ == "__main__":
    main()
