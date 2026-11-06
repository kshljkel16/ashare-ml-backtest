# Build Guide — ML return prediction on CSI 300 with an honest backtest

Same format as your first project. Each step has:
1. **Why**, the problem it solves;
2. **Concepts**, explained from the ground up;
3. **Your task**, with the precise spec in the docstrings of the file you edit;
4. **Done when**, the test that must pass;
5. **Be able to answer**, the interview questions.

**The one idea behind this whole project:** in finance the signal is tiny and the noise is huge, so it is very easy to fool yourself. Almost every step here exists to stop you from fooling yourself: about the future (look-ahead bias), about which stocks existed (survivorship bias), about the test period (leakage), about luck (overfitting), and about money (transaction costs). Interviewers at quant firms test exactly these.

**Time budget:** about 2 weeks at 2–3 hours a day.

---

## Step 0 — Setup and the story

### What you are building
Every week, rank the CSI 300 stocks by how much you expect each one to beat the others over the next 5 trading days. Buy the top fifth. Measure, honestly, whether that ranking is better than a simple momentum rule after trading costs.

This is called **cross-sectional** prediction. You don't predict whether the market goes up; you predict which stocks do *better than the rest*. It's the standard setup for a 量化研究 team, because market direction is close to unpredictable while relative performance is slightly predictable.

### The interview story (fill in at the end)
> "I built a cross-sectional return-prediction pipeline for CSI 300 stocks: point-in-time features, a LightGBM model trained walk-forward with a purge gap, and evaluation by RankIC and a long-only portfolio after transaction costs, against a momentum baseline on the same dates. The model reached a RankIC of X versus Y for momentum; after costs, …"

### Setup
```powershell
cd ashare-ml
git init
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
pytest -q                       # 3 pass, the rest fail: your to-do list
python -m qml.synthetic         # writes data/synthetic.csv so you can look at it
```
Create the GitHub repo **empty** (no README, no .gitignore), name it e.g. `ashare-ml-backtest`, and push. Keep it private until the end.

### The synthetic data, and why it matters
Open `src/qml/synthetic.py`. It makes fake stock prices with **two effects planted on purpose**: momentum (past winners keep winning a little) and short-term reversal (yesterday's jump is partly taken back).

That gives you a **known-answer test**: a correct pipeline *must* find these effects. If your features, labels or backtest can't find a signal you planted yourself, the pipeline is broken, and on real data you would never know. Quant teams do this routinely. Several tests in this project use it.

---

## Step 1 — Data and the label

**Files:** `data.py` (provided, read it); `dataset.py` (you write it)
**Done when:** `pytest tests/test_dataset.py` passes; `python -m qml.data` has downloaded real data to `data/prices.csv`.

### Real data with AkShare
```powershell
python -m qml.data --start 20180101 --end 20251231
```
This downloads about 300 stocks, one file each, into `data/raw/`. If it stops, run it again and it resumes. It takes about 5–15 minutes.

### Concepts

**Adjusted prices (复权).** When a company splits each share in two, the price halves overnight, but nobody lost money. Unadjusted prices show a fake −50% "crash". `hfq` (后复权, backward-adjusted) folds splits and dividends into the history, so returns computed from it are real returns.

**Survivorship bias.** `data.py` downloads *today's* CSI 300 members. A stock that was in the index in 2018 but was dropped because it did badly is missing from your data. Your backtest therefore only contains survivors, which makes the past look better than it was. The fix is point-in-time index membership (which stocks were in the index *on each date*). Free sources rarely have it. **Name this limitation in your README.** Interviewers always ask.

**Suspensions (停牌).** A suspended stock has no trading, and in the data it simply has *no row* that day. That's why everything in this project works on each stock's own *rows* (its trading days), not on calendar days.

### The label: the most important decision in the project
The signal is computed after the **close** of day t. The earliest you can trade on it is the **open** of day t+1. So the return you can actually capture is:
```
fwd_ret[t] = open[t+1+h] / open[t+1] - 1          (h = 5 trading days)
```
A common beginner mistake is `close[t+h] / close[t] - 1`. That assumes you can buy at the very closing price you used to compute the signal, which is impossible. It's a small look-ahead, but on a weak signal it can create a fake edge out of nothing.

**Data leakage, in finance, is called look-ahead bias:** using any information that wasn't available at the moment of the decision.

### Be able to answer
1. Why use adjusted prices? What happens to a momentum feature on a split day without them?
2. What is survivorship bias, which direction does it bias results, and how would you fix it?
3. Why is the label open[t+1] → open[t+1+h], and not close[t] → close[t+h]?

---

## Step 2 — Features

**File:** `features.py`
**Done when:** `pytest tests/test_features.py` passes, **including `test_no_look_ahead`**.

### Concepts
Each feature is a classic, published effect:

| Feature | Formula | The idea |
|---|---|---|
| `mom_20` | 20-day return | Trends persist for a while |
| `rev_5` | minus the 5-day return | Very short-term moves partly reverse; especially strong in A-shares, with many retail traders |
| `vol_20` | 20-day volatility of daily returns | The "low-volatility anomaly": calm stocks often do better per unit of risk |
| `turn_20` | 20-day average turnover | Heavily traded stocks are often overpriced in A-shares |
| `amihud_20` | average \|return\| / amount traded | Illiquidity: how far the price moves per yuan traded |

**Point-in-time.** A feature on day t may use data up to t's close, never later. `test_no_look_ahead` checks this in the strongest way: it changes every price *after* a cut-off date and asserts that no feature *on or before* that date moves at all. If you accidentally use `rolling(..., center=True)`, or a `shift(-1)`, or forget to group by stock, this test catches it.

**Why per stock (`groupby("code")`)?** Without grouping, a 20-day window at the start of stock B would include the last days of stock A. That's a silent bug, and `test_values_on_one_stock` catches it.

**Cross-sectional ranking (`rank_by_date`).** Raw momentum in 2015 (a bubble) and 2018 (a bear market) have completely different ranges. A model trained on raw values learns the market regime, not the stock. Ranking within each day turns every feature into "how does this stock compare with the others *today*", on the same 0–1 scale in every year.

### Be able to answer
1. What does `test_no_look_ahead` do, and why is it a strong test?
2. Why is `rev_5` defined with a minus sign?
3. Why rank features within each date before training?

---

## Step 3 — The baseline and the IC

**File:** `metrics.py`
**Done when:** `pytest tests/test_metrics.py` passes, including `test_planted_signals_are_found`.

### Concepts
**IC (Information Coefficient):** on one date, the correlation across stocks between your signal and the next return. **RankIC** uses Spearman (rank) correlation, which is robust to a single stock jumping 10%.

**What's a good IC?** In equities a daily RankIC of **0.02–0.05 is useful**, and above 0.05 is strong. That sounds tiny, and it is: the signal is weak, but it's applied to hundreds of stocks every week, and small edges compound. If your real-data IC is 0.3, you almost certainly have a look-ahead bug.

**ICIR = mean IC / std of IC:** how *consistent* the signal is. A steady 0.03 beats an erratic 0.05.

**t-stat = mean / std × √n.** Careful: a 5-day label on consecutive days overlaps by 4 days, so daily ICs are correlated and this t-stat **overstates** significance. Mention it; serious researchers correct for it (e.g. Newey–West, or using only non-overlapping dates).

**The baseline is momentum (`mom_20`).** The model is only interesting if it beats a one-line rule. You've done this before: in the first project, the baseline was TF-IDF.

### Be able to answer
1. What is RankIC, and why Spearman rather than Pearson?
2. What IC values are realistic, and what does an IC of 0.3 tell you?
3. Why does the t-stat of daily IC on 5-day labels overstate significance?

---

## Step 4 — Walk-forward training

**File:** `walkforward.py` (`make_splits`, `walk_forward_predict`; `default_model` is provided)
**Done when:** `pytest tests/test_walkforward.py` passes.

### Concepts
**Why not a random split?** In the first project you split by merchant. Here you must split by **time**. A random split puts 2023 days in training and 2021 days in testing, so the model trains on the future. Markets also change over time (regimes), and walk-forward is the only honest simulation of using a model live: train on the past, predict the next months, retrain, move on.

```
|------ train 500 days ------|gap|-- test 60 --|
            |------ train 500 days ------|gap|-- test 60 --|
```

**The purge gap.** The label on the last training day looks 5 days ahead, *into the test period*. Without a gap of at least the horizon, training targets contain test-period prices. That's leakage, and it is subtle enough that many published backtests have it.

**Rank target.** The model predicts the *rank* of the forward return within the day, not its raw value. The raw value is dominated by the market move that day, which no stock feature can predict; the rank is what you actually trade on.

**Why the model is small** (`default_model`):
- `num_leaves=15`: shallow trees;
- `min_child_samples=200`: each leaf must cover many observations;
- `learning_rate=0.03`: small steps;
- `subsample` / `colsample`: randomness that reduces overfitting.

Financial data is mostly noise, so a big model memorises the noise of 2019 and fails in 2020. In finance, simple and regularised usually wins.

**`model_factory`:** the function takes a *factory*, so the tests can pass a fake `MeanModel` that records what it was trained on. It's the same dependency-injection idea as the LLM client in your first project.

### Be able to answer
1. Why walk-forward instead of a random train/test split?
2. What is the purge gap, and what exactly leaks without it?
3. Why train on the per-date rank of returns rather than the raw return?
4. Why a small, heavily regularised model?

---

## Step 5 — From signal to portfolio, and the full research run

**Files:** `portfolio.py` (you write it); `research.py` (provided, it runs everything)
**Done when:** `pytest -q` is all green, and then:
```powershell
python -m qml.research --synthetic     # first: the pipeline must find the planted signal
python -m qml.research                 # then: real CSI 300 data
```

### Concepts
**Quintile portfolios.** On each rebalance date, sort the stocks by signal into 5 groups. If the signal works, the average returns rise from Q1 to Q5 (*monotonic*). A chart of Q1…Q5 is the classic first picture in any factor report.

**Long-short vs long-only.**
- **Long-short (Q5 − Q1)** measures signal quality. But **shorting A-shares is heavily restricted**, so it isn't a strategy you could actually run.
- **Long-only excess (Q5 − equal-weight universe), after costs** is the realistic version. Say this distinction in interviews; it shows you know the market.

**Turnover and costs.** Rebalancing weekly means replacing part of the portfolio every week. Each replacement is a sell plus a buy, so the cost is `2 × cost_one_way × turnover`. `config.COST_ONE_WAY = 0.0015` (15 basis points) is an *assumption*, which is why the report also shows 0, 5, 15 and 30 bp. **A signal that only works at 0 bp costs doesn't work.** In the synthetic run you'll see costs roughly halve the model's Sharpe ratio. Turnover is often what kills a strategy.

**Sharpe ratio** = mean / std of period returns × √(periods per year): return per unit of risk. With 5-day periods there are 50 periods a year.

**Max drawdown** = the worst fall from a previous peak, i.e. the pain an investor would have lived through.

**Same dates.** `research.py` evaluates the baseline and the model on exactly the out-of-sample dates the model produced. Comparing a model's 2022–2025 with a baseline measured on 2018–2025 would be comparing different markets.

### What to expect on real data
Something like a RankIC of 0.01–0.04, and a long-only excess return that is small, possibly negative, after costs. **That is a normal, honest result.** Your write-up is about the method and what you found, not about a big number. A result that looks too good is the first thing to distrust.

### Be able to answer
1. Long-short vs long-only: which is tradable in A-shares, and why?
2. How do you compute transaction costs from turnover?
3. Your model has a higher IC than momentum but a lower net return. How can that happen? (Hint: turnover.)
4. Your backtest shows a Sharpe of 3 on real data. What do you check first?

---

## Step 6 — Extension: LLM sentiment from announcements (公告)

Once Steps 1–5 work on real data, add one AI feature: classify each stock's company announcements with Kimi (positive / neutral / negative, plus an event type), and test whether that feature improves RankIC. You'll reuse your first project's LLM pipeline: batching, caching, validated JSON and cost tracking.

The trap here is **timestamps**. An announcement published at 20:00 on day t can only be traded at the open of day t+1, so it belongs to day t's features only if it was published before the close. Getting this wrong is look-ahead bias again.

We'll scaffold this step together when you get there.

---

## Step 7 — Write-up

README with: the results table (baseline vs model, same dates); the three charts; design decisions with evidence; and limitations:
- survivorship bias;
- one market and one period;
- the cost assumption;
- daily data only;
- overlapping labels in the t-stat.

Then a CV bullet with your real numbers, and the 60-second pitch.

## Extensions, if you have time
- Point-in-time index membership to remove survivorship bias.
- Industry neutralisation: rank within each industry, so the model doesn't just bet on sectors.
- Newey–West t-stat for overlapping labels.
- Feature importance across walk-forward windows: which features are stable?
- A turnover penalty: only trade when the signal changes enough to pay the cost.
