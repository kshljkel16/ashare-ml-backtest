"""Project-wide settings. Every assumption lives here, in one place, with its reason.

Change a value here, rerun, and every step uses it — never hard-code these elsewhere.
"""

# Prediction horizon in trading days: we predict the return over the next 5 days (one week).
HORIZON = 5

# Rebalance the portfolio every HORIZON days, so holding periods do not overlap
# (overlapping periods would count the same return several times).
REBALANCE_EVERY = HORIZON

# Stocks are split into this many groups by signal (quintiles): Q1 = lowest, Q5 = highest.
N_QUANTILES = 5

# A date needs at least this many stocks with a signal and a label to compute an IC.
MIN_STOCKS_PER_DATE = 20

# One-way trading cost as a fraction of the traded amount: 0.0015 = 15 basis points.
# ASSUMPTION — roughly commission (~2.5 bp) + half of the 5 bp stamp duty on sells
# + slippage/market impact (~10 bp) for liquid CSI 300 names. Check current broker rates;
# Step 5 reports results at several cost levels so the conclusion does not hinge on this number.
COST_ONE_WAY = 0.0015

# Walk-forward windows, in trading days (~250 per year).
TRAIN_DAYS = 500      # ~2 years of history to train on
TEST_DAYS = 60        # ~3 months predicted before the model is retrained

# The features built in Step 2. Every model and report uses this list.
FEATURES = ["mom_20", "rev_5", "vol_20", "turn_20", "amihud_20"]
