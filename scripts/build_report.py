"""Generate checked-in findings from the fictional demo using shared metrics."""
from pathlib import Path
import math
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.analytics import kpis, opportunity_lists, risk_by_group, segment_summary
from utils.data_loader import ROOT, load_data
from utils.segmentation import customer_profile


def build_report():
    bundle = load_data(ROOT / "data" / "demo")
    trans = bundle.transactions
    metrics = kpis(trans)
    profile = customer_profile(trans, bundle.users, bundle.cards)
    retention, cross_sell = opportunity_lists(profile)
    spend = trans.loc[trans.is_purchase].groupby("client_id")["amount"].sum().sort_values(ascending=False)
    n_top = math.ceil(len(spend) * 0.2)
    top_share = spend.head(n_top).sum() / spend.sum()
    risk = risk_by_group(trans, "merchant_category")
    highest = risk.iloc[0]
    lines = [
        "# Reproducible demo findings", "",
        "**Scope: entirely fictional data, seed 42. No real-world commercial result is claimed.**", "",
        "Regenerate with `python scripts/build_report.py`. The report uses the full transaction period and a 365-day RFM window ending the day after the final observed transaction.", "",
        "| Measure | Demo result |", "| --- | ---: |",
        f"| Transactions | {len(trans):,} |",
        f"| Customers in registry | {len(bundle.users):,} |",
        f"| Gross purchase value | ${metrics['purchase_value']:,.2f} |",
        f"| Refund/reversal value | ${metrics['refund_value']:,.2f} |",
        f"| Net transaction value | ${metrics['net_value']:,.2f} |",
        f"| Known-label coverage | {metrics['label_coverage']:.2%} |",
        f"| Observed fraud cases | {metrics['fraud_count']} |",
        f"| Fraud rate among known labels | {metrics['fraud_rate']:.2%} |", "",
        "## Findings and next steps", "",
        f"1. The top {n_top} purchasing customers (approximately 20%) account for **{top_share:.1%}** of purchase value. A retention pilot could prioritize valuable customers while tracking incentive cost; concentration does not prove an 80/20 rule.",
        f"2. RFM identifies **{len(retention)} at-risk customers** in the full-registry analysis. This is a rule-based classification, not observed future churn. A randomized reactivation pilot would test whether outreach changes behavior.",
        f"3. **{len(cross_sell)} active customers** meet the top-quartile spending/no-existing-Credit-card discovery rule. This is not underwriting eligibility or expected conversion.",
        f"4. **{highest['merchant_category']}** has the highest observed category fraud rate in this artificial sample: **{highest['rate']:.2%}**, based on {int(highest['labeled'])} labeled transactions. The Wilson 95% interval is [{highest['ci_low']:.2%}, {highest['ci_high']:.2%}]. Differences need further investigation and are not causal.",
        f"5. **{trans['is_fraud'].isna().sum()} transactions have unknown labels**. They remain outside fraud-rate denominators. Source-wide rates may differ if labeling is selective.", "",
        "## RFM composition", "",
        "| Segment | Customers | Purchase value in window |", "| --- | ---: | ---: |",
    ]
    for row in segment_summary(profile).itertuples():
        lines.append(f"| {row.Segment} | {row.customers} | ${row.purchase_value:,.2f} |")
    lines += ["", "The dashboard's default customer cohort includes customers seen in its transaction scope; this report includes the entire registry, including customers with no transaction history. That difference is intentional.", "",
              "## Limits", "", "Artificial generation rules drive these findings. They demonstrate reproducibility and analytical reasoning, not actual financial-sector behavior. No trained fraud model, real customer campaign, measured uplift or full-scale performance benchmark is provided.", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    path = ROOT / "docs" / "DEMO_FINDINGS.md"
    path.write_text(build_report(), encoding="utf-8", newline="\n")
    print(path)
