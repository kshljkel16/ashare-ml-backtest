# Step 5 — Portfolio results (out-of-sample 2020-02 to 2025-12, 15 bp one-way costs)

Pipeline check: synthetic run matches the reference exactly (model RankIC 0.0566, LS Sharpe 4.25).

| | RankIC | LS Sharpe (gross) | Long-only excess, net | Net Sharpe | Turnover |
|---|---|---|---|---|---|
| Momentum baseline | -0.014 | 0.18 | +0.2%/yr | 0.08 | 0.36 |
| Model | 0.021 | -0.19 | -5.4%/yr | -0.59 | 0.39 |

Model quintiles (5-day forward return, rebalance dates):
| Q | Mean | Median | Std |
|---|---|---|---|
| Q1 | 0.45% | -0.19% | 6.7% |
| Q2 | 0.35% | -0.07% | 5.4% |
| Q3 | 0.33% | -0.10% | 5.3% |
| Q4 | 0.34% | 0.00% | 5.1% |
| Q5 | 0.38% | 0.00% | 5.5% |

- Ranking works in the median (Q1 -0.19% -> Q5 0.00%), which is what the positive RankIC measures.
- Mean returns don't follow: Q1 holds volatile, high-turnover "lottery" stocks (highest std); most
  lose, a few jump, and the right skew lifts Q1's mean. Shorting Q1 loses -> negative LS Sharpe.
- Tradable edge (Q5 minus universe) ~ +0.01%/week ~ +0.5%/yr gross; costs = 2 x 15 bp x 0.39
  turnover x 50 weeks ~ 5.8%/yr -> net -5.4%/yr.
- RankIC on rebalance dates only: 0.0168 (vs 0.0213 on all dates) — some sampling noise.
- Conclusion: positive IC is necessary but not sufficient; skew and turnover separate ranking skill
  from net returns.