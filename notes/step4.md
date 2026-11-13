# Step 4 — Walk-forward model (out-of-sample 2020-02-05 to 2025-12-31, 24 retrains)

| Signal (same dates) | Mean RankIC | ICIR | Hit rate |
|---|---|---|---|
| **model (LightGBM)** | **0.0213** | **0.125** | **0.554** |
| mom_20 (baseline) | -0.0140 | -0.066 | 0.493 |
| rev_5 | 0.0096 | 0.050 | 0.496 |
| vol_20 | -0.0233 | -0.083 | 0.455 |
| turn_20 | -0.0292 | -0.114 | 0.451 |
| amihud_20 | 0.0174 | 0.132 | 0.551 |

- Model beats the pre-chosen momentum baseline clearly.
- It does NOT beat the best single factor in hindsight (|turn_20 IC| 0.029; amihud ICIR 0.132),
  but those require knowing the sign in advance (snooping). The model learned directions from the
  past only and roughly matches the best factor without hindsight.
- Lower IC std (0.17) than most single features: combining weak signals diversifies their errors.
- t-stat 4.7 overstated by overlapping labels; ~2.1 after dividing by sqrt(5).
- Open question for Step 5: does an IC of ~0.02 survive turnover and trading costs?

## Interview answers
1. Walk-forward, not random split: a random split trains on future days and tests on past ones,
   and ignores that markets change; walk-forward simulates live use (train on past, predict next
   months, retrain).
2. Purge gap: the last training label looks HORIZON days ahead. With gap = horizon, the last training
   label ends at the open of the first test day, before any test label begins; without it, training
   targets contain test-period prices.
3. Rank target: the raw return is dominated by the day's market move, which stock features can't
   predict; the per-date rank is what we trade on.
4. Small, regularised model: signal-to-noise is tiny, so a flexible model memorises noise from its
   training years; shallow trees, large leaves, low learning rate and subsampling keep it simple.