# Analytical methodology

## Questions
1. How do transaction counts and net values change over time?
2. How concentrated is customer spending?
3. Which customers have recent/high-frequency/high-value purchase behavior?
4. How do observed fraud rates vary across sufficiently sampled groups?
5. Which cohorts could support a reactivation or credit-card discovery experiment?

## Metric definitions
| Metric | Definition |
| --- | --- |
| Purchase | amount > 0 and no transaction error |
| Gross purchase value | Sum of eligible positive amounts |
| Refund/reversal value | Absolute sum of negative amounts without errors |
| Net transaction value | Sum of all amounts without errors |
| Average purchase | Gross purchase value / purchase count |
| Purchasing customer | Distinct customer with at least one purchase |
| Fraud rate | Sum of known binary labels / number of known labels |
| Coverage | Known labels / all transactions in the selected scope |
| Concentration | Purchase value of the top ceil(20% × purchasing customers) / total purchase value |

Source text values empty, No Error, None and nan are interpreted as no error. All other error strings indicate an error.

Transaction value is not interchange income, merchant revenue, profit or realized fraud loss. No LTV is estimated without a defensible model of revenue, margin, retention and discounting.

## RFM
The reference timestamp is midnight on the day after the selected end date. The interval is **[reference minus lookback days, reference)**. Eligible records are positive, error-free purchases.

- Recency: whole elapsed days from the latest eligible purchase to the reference.
- Frequency: eligible transaction count.
- Monetary: sum of eligible purchase amounts.

Average ranks preserve ties. With n customers and average rank r, normalized rank is (r−1)/(n−1); score = min(floor(5 × normalized rank), 4)+1. Recency scores are reversed. A constant feature receives neutral score 3. Ties can produce unequal bin sizes; this is intentional. Scores describe relative standing, not calibrated probabilities.

Rules, in priority order:

| Rule | Segment |
| --- | --- |
| R ≤ 2 and F ≥ 3 or M ≥ 3 (within the low-R group) | At risk |
| R ≤ 2 otherwise | Hibernating |
| R ≥ 4 and F ≥ 4 and M ≥ 4 | Champions |
| F ≥ 4 | Loyal |
| M ≥ 4 | High spenders |
| R ≥ 4 | Promising |
| Otherwise | Needs attention |
| No eligible purchases | No purchases in window |

The first rule means `R <= 2 and (F >= 3 or M >= 3)`. The low-recency branch precedes loyal/high-spender rules.

The UI transaction filters define the customer cohort. RFM then uses **all cards** belonging to those customers within its own lookback, which may begin before the visible transaction start date. Customers with unmatched user IDs remain in transaction KPIs but cannot appear in registry-based customer profiles. The notebook full-registry analysis also includes customers with no transaction history.

## Fraud analysis
Rates use known labels only, without imputing missing labels. Groups require at least 30 labeled transactions by default. Wilson intervals use z=1.96.

Intervals assume independent Bernoulli observations; repeated customers, selection bias, temporal clustering and multiple comparisons weaken that assumption. Wide intervals and low coverage should reduce confidence. Group associations do not identify causes.

There is no trained fraud model, holdout evaluation or production deployment. A future ML extension should use chronological validation, a leakage audit, an appropriate baseline, PR-AUC and a threshold/cost analysis.

## Candidate actions
- Retention: At-risk customers sorted by purchase value within the RFM window.
- Credit-card discovery: active customers at/above the 75th percentile of purchase value, without a Credit card anywhere in the supplied registry.
- The SQL cross-sell example uses PERCENT_RANK, while the dashboard uses interpolated pandas quantiles; boundary ties/small cohorts may differ. This distinction is documented, not hidden.

Lists are marketing hypotheses. Eligibility, consent, current ownership and credit policy require separate verification. Proposed metrics: incremental 30-day reactivation, application completion, incentive cost and incremental contribution after costs. No experiment or uplift is claimed.

## Verification and limits
Unit tests cover unknown labels, duplicate keys, ownership mismatches, refunds/errors, tied scores, temporal boundaries and no-purchase cohorts. SQLite queries are checked against Python monthly metrics, fraud rates and raw RFM. Streamlit AppTest exercises filters, downloads, missing inputs and empty groups.

The included sample demonstrates functionality. It does not validate the representativeness of the old course dataset or prove that these business rules improve real outcomes.
