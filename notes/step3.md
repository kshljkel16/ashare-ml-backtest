# Step 3 — IC on real data (CSI 300, 2018–2025, full period = in-sample, exploration only)

| Feature | Mean RankIC | ICIR | Hit rate |
|---|---|---|---|
| mom_20 | -0.0144 | -0.070 | 0.491 |
| rev_5 | 0.0104 | 0.055 | 0.503 |
| vol_20 | -0.0145 | -0.052 | 0.476 |
| turn_20 | -0.0216 | -0.084 | 0.468 |
| amihud_20 | 0.0166 | 0.114 | 0.548 |

- Momentum is reversed at 1 month in A-shares (negative IC); short-term reversal works weakly.
- Low-volatility anomaly (vol_20 negative), turnover effect (turn_20 most negative — attention-driven
  retail trading), illiquidity premium (amihud_20 positive and most consistent).
- Signals are weak and noisy: means 0.01–0.02 vs daily IC std 0.15–0.28; hit rates near 50%.
- Reported t-stats (2–5) are overstated: overlapping 5-day labels -> ~5x fewer independent
  observations; dividing by ~sqrt(5) gives ~1–2.2.
- These ICs are in-sample: NOT used to pick features or flip signs (data snooping). The model learns
  directions inside each walk-forward window. Baseline stays momentum (fixed before seeing data);
  the real bar is long-only top quintile vs the equal-weight universe after costs.

## Interview answers
1. RankIC = per-date Spearman correlation between signal and next return across stocks; ranks make
   it robust to outlier returns (right-skewed, up to +218% here).
2. Realistic daily RankIC in equities: 0.02–0.05 useful. An IC of 0.3 almost certainly means a
   look-ahead bug.
3. Daily ICs on 5-day labels overlap by 4 days, so they are correlated; the naive t-stat treats them
   as independent and overstates significance (fix: non-overlapping dates or Newey-West).