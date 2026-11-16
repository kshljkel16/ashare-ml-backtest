"""Compare Kimi's labels with a second LLM (Claude), labelled blind from titles only."""
import pandas as pd

PATH = "reports/event_study_20240101_20241231/label_check.csv"

# Claude's blind labels, in the same row order as label_check.csv (rows 1..50)
CLAUDE = [0, 0, 0, 0, 0, -1, 0, 0, 1, 0,
          0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
          0, 0, 0, 0, 0, 0, 0, 0, 0, -1,
          1, 0, 1, 1, 0, 0, 0, 0, 0, 0,
          0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

d = pd.read_csv(PATH, dtype={"code": str})
assert len(d) == 50, f"expected 50 rows, found {len(d)}"
assert d.loc[8, "title"].find("政府补助") >= 0, "row order differs from the list Claude labelled"
d["claude_sentiment"] = CLAUDE
d.to_csv(PATH, index=False, encoding="utf-8-sig")

llm = d["llm_sentiment"].astype(int)
agree = (d["claude_sentiment"] == llm).mean()
print(f"Claude vs Kimi agreement: {agree:.0%} on {len(d)} titles\n")
print("Rows = Claude, columns = Kimi:")
print(pd.crosstab(d["claude_sentiment"], llm))

nonneutral = (d["claude_sentiment"] != 0) | (llm != 0)
print(f"\nAgreement where at least one of them said non-neutral: "
      f"{(d.loc[nonneutral, 'claude_sentiment'] == llm[nonneutral]).mean():.0%} "
      f"({nonneutral.sum()} titles)")
print("\nDisagreements:")
for i, r in d[d["claude_sentiment"] != llm].iterrows():
    print(f"  row {i + 1}: Claude {r.claude_sentiment:+d}, Kimi {int(r.llm_sentiment):+d}:  {r.title}")