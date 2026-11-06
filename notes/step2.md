# Step 2 — Features

- Missing: 1.1% for 20-day features, 0.3% for rev_5 (first rows of each stock + a 21-day listing).
- Long tails: mom_20 max +573%, rev_5 min -2.22 (+222% in 5 days), amihud_20 max 56 vs median 0.03
  — IPO and suspension cases from Step 1. Ranking per date makes them harmless.
- Spearman correlations: mom_20 vs rev_5 = -0.43 (last 5 days are inside the last 20);
  vol_20 vs turn_20 = 0.71 (in A-shares volatile stocks are the heavily traded ones —
  speculative retail trading); amihud_20 is the most independent (|corr| <= 0.15).
  Five features, but fewer than five independent signals.
- Bug I made and fixed: ranking with groupby("code") ranks a stock against its own whole history,
  including future days -> look-ahead. Within a stock, only look back; ranks/z-scores belong to
  groupby("date").

## Interview answers
1. test_no_look_ahead changes every price after a cut-off date and checks that all features on or
   before it are exactly unchanged — catches shift(-1), centred windows, whole-series statistics.
2. rev_5 has a minus sign so that for every feature, higher = expected to do better: recent losers
   tend to bounce, so the most negative 5-day return gets the highest rev_5. A working feature then
   has a positive IC and its top quintile is the one to buy.
3. Rank within each date: (a) comparable across regimes — raw momentum ranges differ by year;
   (b) robust to outliers (+573% momentum becomes "highest today"); (c) matches what we trade —
   relative ranking of stocks on a day.