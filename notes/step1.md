# Step 1 — Data and label

- Source: AkShare, 后复权 (hfq) daily prices for today's 300 CSI 300 members, 2018-01-02 to 2025-12-31.
  535,418 rows; cleaning removed 0 rows (AkShare already omits suspended days; no duplicates).
- History length: median 1,942 trading days; min 21 (a stock listed ~Dec 2025). Short histories
  give NaN features at first.
- Only 2 daily moves beyond ±21% (main-board limit ±10%, ChiNext/STAR ±20%):
  - 688256, 2020-07-21: STAR stock in its first 5 trading days after IPO (no price limit).
  - 000792, 2021-08-10: first day after a long suspension (no limit on resumption).
  Code works on rows (trading days), so after a long suspension "the next row" can be months
  later: that row's return and any label spanning it cover the whole suspension. Rare (2 / 535k);
  rank-based metrics are robust to it. Possible fix: flag labels whose calendar span is too long.
- fwd_ret (5-day, next open -> open): mean +0.34%, median -0.04% (right-skewed), std 5.8%,
  min -42%, max +218% (likely the suspension case). The mean (~18%/yr) is high: dividends in
  hfq prices plus survivorship bias (only today's members, i.e. the winners that stayed in).

## Interview answers
1. **Adjusted prices:** a split halves the share price with no loss to investors; unadjusted
   prices show a fake -50% "crash" that would poison momentum and returns. hfq folds splits and
   dividends into the history, so returns from it are real total returns.
2. **Survivorship bias:** the universe is today's index; stocks removed since 2018 (often for
   doing badly) are missing, so the backtest sees only survivors and looks better than reality.
   Visible here in the high average return. Fix: point-in-time index membership per date.
3. **Label open[t+1] -> open[t+1+h]:** the signal is only known after day t's close, so the first
   possible trade is the next open. close[t] -> close[t+h] assumes buying at the very price used
   to compute the signal — a small look-ahead that can create a fake edge on a weak signal.