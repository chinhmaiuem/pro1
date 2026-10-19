# LedgerLens · Transaction Analytics
A Python + SQL portfolio for exploring card transactions, segmenting customers and turning descriptive findings into testable business actions.

**Scope:** Data Analyst / junior analytics portfolio. Rule-based RFM and exploratory fraud analysis; no trained fraud classifier and no claimed production impact.

## Run in three steps

Use **Python 3.12 or 3.13**. A fictional demo is included; no download, credentials or large external dataset is needed.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Optional validation:
```bash
python check_setup.py
python -m unittest discover -s tests -v
python scripts/run_sql.py
```

## What is implemented

| Area | Delivered behavior |
| --- | --- |
| Overview | Period/card filters, net value, purchase/refund reconciliation, monthly trends, measured spending concentration |
| Customer segments | One shared RFM implementation, explicit lookback window, tie-safe scoring, segment comparison and CSV export |
| Fraud patterns | Known-label denominator, label coverage, minimum group sizes, Wilson intervals and downloadable comparisons |
| Business actions | At-risk reactivation and credit-card discovery cohorts, transparent eligibility rules and pilot metrics |
| Data quality | Schema/key validation, ownership-aware card joins, unmatched references and unknown-label reporting |
| SQL | Executable joins, CTEs, aggregations, window functions and an ownership exclusion query |

Every tab contains an implemented analysis, with a documented denominator and scope.

## Demo findings

The seeded demo contains **6,000 transactions and 240 fictional customers**. Its purchase value, refunds and fraud rates are artificial examples, not real banking results. See the [reproducible findings](docs/DEMO_FINDINGS.md) and [methodology](docs/METHODOLOGY.md).

Regenerate the exact demo and report:
```bash
python scripts/generate_demo.py
python scripts/build_report.py
```

## Use your own local data

Choose **Local dataset** in the sidebar and point to a folder following [the data contract](docs/DATA.md). The default folder is `data/full/`, which is ignored by Git. Missing fraud labels do not prevent spending analysis.

The older root CSVs containing card/contact fields have been removed from this proposed version. They are not required for the fictional demo; prior commits retain project history. No origin, license or authenticity of those old datasets is asserted.

## Project layout

```text
app.py                    Streamlit application
utils/data_loader.py      Validation and analytical joins
utils/segmentation.py     Shared RFM scoring and customer profiles
utils/analytics.py        Metrics, risk rates and candidate rules
utils/visualizations.py   Plotly presentation helpers
data/demo/                Reproducible fictional inputs
scripts/                  Demo generation, SQL runner, findings report
sql/                      Four executable SQLite analyses
tests/                    Analytical regression and dashboard interaction tests
docs/                     Data contract, methodology and findings
1.ipynb                   Walkthrough using the same production functions
```

## Decisions and limitations

- Transaction value is **not bank revenue**. Negative amounts are treated as refunds/reversals; errored rows are excluded from settled value.
- Unknown fraud labels are excluded from the rate denominator and reported as coverage gaps.
- RFM uses successful positive purchases in an explicit window. Scores are relative to the customer cohort.
- Credit ownership comes from the complete supplied card registry, including cards not used during the selected period.
- Candidate lists support experiments; they are not underwriting or fraud decisions.
- Customer financial/demographic attributes are snapshots; use them cautiously for historical analysis.
- SQL and Python checks validate key metric consistency. Full-scale performance on the external 300MB+ dataset has not been benchmarked.

## Background and ownership

This repository began as a COLE.VN DS K06 Module 2 course project. The portfolio revision consolidates its analysis into a reproducible application with explicit metric contracts. Describe your own implementation and understanding accurately when discussing it in interviews; the original coursework remains in Git history.

No license for third-party source data is implied. The demo is generated entirely by `scripts/generate_demo.py`; see [data provenance](docs/DATA.md).
