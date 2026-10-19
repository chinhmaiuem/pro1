# Reproducible demo findings

**Scope: entirely fictional data, seed 42. No real-world commercial result is claimed.**

Regenerate with `python scripts/build_report.py`. The report uses the full transaction period and a 365-day RFM window ending the day after the final observed transaction.

| Measure | Demo result |
| --- | ---: |
| Transactions | 6,000 |
| Customers in registry | 240 |
| Gross purchase value | $713,473.03 |
| Refund/reversal value | $16,578.72 |
| Net transaction value | $696,894.31 |
| Known-label coverage | 93.82% |
| Observed fraud cases | 62 |
| Fraud rate among known labels | 1.10% |

## Findings and next steps

1. The top 48 purchasing customers (approximately 20%) account for **64.5%** of purchase value. A retention pilot could prioritize valuable customers while tracking incentive cost; concentration does not prove an 80/20 rule.
2. RFM identifies **41 at-risk customers** in the full-registry analysis. This is a rule-based classification, not observed future churn. A randomized reactivation pilot would test whether outreach changes behavior.
3. **37 active customers** meet the top-quartile spending/no-existing-Credit-card discovery rule. This is not underwriting eligibility or expected conversion.
4. **Electronics** has the highest observed category fraud rate in this artificial sample: **1.80%**, based on 888 labeled transactions. The Wilson 95% interval is [1.11%, 2.91%]. Differences need further investigation and are not causal.
5. **371 transactions have unknown labels**. They remain outside fraud-rate denominators. Source-wide rates may differ if labeling is selective.

## RFM composition

| Segment | Customers | Purchase value in window |
| --- | ---: | ---: |
| At risk | 41 | $70,962.40 |
| Champions | 51 | $204,587.01 |
| Hibernating | 48 | $9,071.30 |
| High spenders | 6 | $8,759.93 |
| Loyal | 29 | $41,910.94 |
| Needs attention | 20 | $9,684.81 |
| No purchases in window | 16 | $0.00 |
| Promising | 29 | $11,975.45 |

The dashboard's default customer cohort includes customers seen in its transaction scope; this report includes the entire registry, including customers with no transaction history. That difference is intentional.

## Limits

Artificial generation rules drive these findings. They demonstrate reproducibility and analytical reasoning, not actual financial-sector behavior. No trained fraud model, real customer campaign, measured uplift or full-scale performance benchmark is provided.
