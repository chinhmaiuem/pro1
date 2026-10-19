"""LedgerLens — a reproducible transaction analytics portfolio."""
from pathlib import Path
import math

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.analytics import kpis, monthly_summary, opportunity_lists, risk_by_group, safe_csv, segment_summary
from utils.data_loader import ROOT, DataValidationError, file_signature, load_data
from utils.segmentation import customer_profile
from utils.visualizations import PALETTE, monthly_chart, polish, segment_chart

st.set_page_config(page_title="LedgerLens | Transaction Analytics", page_icon="◈", layout="wide")
st.markdown("""
<style>
.stApp {background: #f5f7f8;}
.block-container {padding-top: 2.4rem; max-width: 1450px;}
h1, h2, h3 {color: #183745;}
div[data-testid="stMetric"] {background: white; border: 1px solid #e0e7e8; border-radius: 12px; padding: 18px;}
div[data-testid="stMetricLabel"] {color: #61737b;}
.hero-label {color:#127f80; letter-spacing: .15em; font-size:.78rem; font-weight:700;}
.hero-copy {color:#61737b; max-width:760px; line-height:1.6; margin-bottom: 1.3rem;}
section[data-testid="stSidebar"] {background: #eaf0f1;}
</style>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner=False, max_entries=3)
def cached_data(directory, signature):
    # Signature is intentionally hashed: changed files invalidate cached datasets.
    return load_data(directory)


def chart(fig, key):
    st.plotly_chart(fig, width="stretch", key=key, config={"displaylogo": False})


def table(frame, **kwargs):
    st.dataframe(frame, width="stretch", hide_index=True, **kwargs)


def download(frame, label, filename, key):
    st.download_button(label, safe_csv(frame), filename, "text/csv", key=key)


def usd(value):
    return f"${value:,.0f}"


with st.sidebar:
    st.markdown("## ◈ LedgerLens")
    st.caption("TRANSACTION INTELLIGENCE")
    mode = st.selectbox("Data source", ["Synthetic demo", "Local dataset"], key="source")
    if mode == "Synthetic demo":
        directory = ROOT / "data" / "demo"
        st.caption("240 fictional customers · 2018–2019")
    else:
        folder = st.text_input("Dataset folder", "data/full", help="Relative to the project folder, or an absolute local path.")
        directory = Path(folder)
        if not directory.is_absolute():
            directory = ROOT / directory
    if st.button("Reload data", width="stretch"):
        cached_data.clear()
    st.divider()
    st.caption("Built with Python, pandas, SQL, Streamlit and Plotly.")
    st.caption("Exploratory analysis · no trained fraud model")

st.markdown('<div class="hero-label">PORTFOLIO / CUSTOMER ANALYTICS</div>', unsafe_allow_html=True)
st.title("Transactions into decisions.")
st.markdown('<div class="hero-copy">Explore spending patterns, understand customer segments and prioritize the next business question — with traceable metrics and explicit data quality checks.</div>', unsafe_allow_html=True)

try:
    with st.spinner("Validating and preparing data…"):
        bundle = cached_data(str(directory.resolve()), file_signature(directory))
except (DataValidationError, ValueError, OSError, pd.errors.ParserError) as exc:
    st.error(f"Cannot load this dataset: {exc}")
    st.info("Use Synthetic demo, or follow docs/DATA.md to prepare a local dataset.")
    st.stop()

raw = bundle.transactions
is_demo = directory.resolve() == (ROOT / "data" / "demo").resolve()
if is_demo:
    st.info("SYNTHETIC DEMO · All records are generated for this portfolio. Findings describe this fictional sample only.")
else:
    st.warning("LOCAL DATA · Confirm provenance and permitted use. Sampling and label coverage can affect every conclusion.")

with st.sidebar:
    st.markdown("### Analysis scope")
    dates = st.date_input("Transaction period", value=(raw["date"].min().date(), raw["date"].max().date()),
                          min_value=raw["date"].min().date(), max_value=raw["date"].max().date())
    types = sorted(raw["card_type"].dropna().unique().tolist())
    selected_types = st.multiselect("Card types", types, default=types, key="card_types")
    window_days = st.selectbox("RFM lookback · days", [365, 180, 90], key="lookback", help="Measured backwards from the day after the selected period ends.")
    st.caption("Period and card filters apply to transaction views. RFM uses all card types for customers seen in that filtered scope.")

if len(dates) != 2:
    st.info("Select both a start date and an end date.")
    st.stop()
start, end = pd.Timestamp(dates[0]), pd.Timestamp(dates[1]) + pd.Timedelta(days=1)
scope = raw.loc[raw["date"].ge(start) & raw["date"].lt(end) & raw["card_type"].isin(selected_types)].copy()
if scope.empty:
    st.info("No transactions match these filters. Expand the period or select a card type.")
    st.stop()

# Cohort membership follows the scope; RFM uses complete customer history up to the cutoff,
# not only a selected card, which would misclassify multi-card customers.
cohort_ids = scope["client_id"].unique()
users = bundle.users.loc[bundle.users["id"].isin(cohort_ids)]
history = raw.loc[raw["client_id"].isin(cohort_ids)]
profile = customer_profile(history, users, bundle.cards, end, window_days)
metrics = kpis(scope)
summary = segment_summary(profile)
retention, cross_sell = opportunity_lists(profile)
coverage = metrics["label_coverage"]
st.caption(f"{dates[0]:%d %b %Y} — {dates[1]:%d %b %Y}  /  {len(scope):,} transactions  /  {len(users):,} matched customers  /  USD")

cols = st.columns(4)
for col, name, value in zip(cols,
                            ["Net transaction value", "Purchasing customers", "Average purchase", "Fraud rate · labeled only"],
                            [usd(metrics["net_value"]), f'{scope.loc[scope["is_purchase"], "client_id"].nunique():,}',
                             usd(metrics["avg_purchase"]), f'{metrics["fraud_rate"]:.2%}' if metrics["fraud_rate"] is not None else "N/A"]):
    col.metric(name, value)
st.caption(f'Net value = successful purchases {usd(metrics["purchase_value"])} − refunds/reversals {usd(metrics["refund_value"])}. Label coverage: {coverage:.1%}. Transaction value is not bank revenue.')

overview, segments, risk, actions, quality = st.tabs(["Overview", "Customer segments", "Fraud patterns", "Business actions", "Data & methodology"])

with overview:
    left, right = st.columns([1.6, 1])
    with left:
        st.subheader("Value over time")
        chart(monthly_chart(monthly_summary(scope)), "monthly")
    with right:
        st.subheader("Customer composition")
        chart(segment_chart(summary), "composition")
    left, right = st.columns(2)
    purchases = scope.loc[scope["is_purchase"]]
    with left:
        st.subheader("Where customers spend")
        categories = purchases.groupby("merchant_category", as_index=False)["amount"].sum().nlargest(8, "amount").sort_values("amount")
        fig = px.bar(categories, x="amount", y="merchant_category", orientation="h", color_discrete_sequence=PALETTE)
        fig.update_layout(xaxis_title="Purchase value · USD", yaxis_title=None)
        chart(polish(fig), "categories")
    with right:
        st.subheader("Concentration, measured")
        spend = purchases.groupby("client_id")["amount"].sum().sort_values(ascending=False)
        n_top = max(1, math.ceil(len(spend) * 0.2))
        share = spend.head(n_top).sum() / spend.sum() if spend.sum() else 0
        st.metric(f"Top {n_top} purchasing customers' share", f"{share:.1%}")
        st.write(f"The top approximately 20% account for {share:.1%} of positive, error-free purchase value in this scope.")
        st.caption("This is a measured concentration statistic; the data is not assumed to follow an 80/20 rule.")
        method = purchases.groupby("use_chip", as_index=False).size()
        if not method.empty:
            chart(polish(px.bar(method, x="use_chip", y="size", color_discrete_sequence=[PALETTE[1]]), height=240), "methods")

with segments:
    st.subheader("A consistent RFM view")
    st.write(f"Window: {(end - pd.Timedelta(days=window_days)).date()} to {end.date()} (exclusive). Purchase activity across all cards; matched customers in the selected scope.")
    st.caption("Recency = days since latest purchase. Frequency = purchase count. Monetary = gross purchase value. Refunds and error rows are excluded. Equal values receive equal scores.")
    table(summary, column_config={"purchase_value": st.column_config.NumberColumn(format="$%.2f")})
    active = profile.loc[profile["Frequency"] > 0]
    if not active.empty:
        fig = px.scatter(active, x="Frequency", y="Monetary", color="Segment",
                         hover_data=["client_id", "Recency"], color_discrete_sequence=PALETTE, log_y=True)
        chart(polish(fig, height=400), "rfm_scatter")
    segment_filter = st.multiselect("Inspect customer segments", sorted(profile["Segment"].unique()), default=[])
    inspected = profile.loc[profile["Segment"].isin(segment_filter)] if segment_filter else profile
    export_cols = ["client_id", "Segment", "Recency", "Frequency", "Monetary", "R_Score", "F_Score", "M_Score", "has_credit_card"]
    table(inspected[export_cols])
    download(inspected[export_cols], "Download customer segments", "customer_segments.csv", "segments_csv")
    st.caption("Rule-based segmentation, not machine learning. Customers absent from the filtered transaction cohort are not shown; the quality tab reports the full registry.")

with risk:
    st.subheader("Observed fraud, with the denominator")
    a, b, c = st.columns(3)
    a.metric("Labeled transactions", f'{scope["is_fraud"].notna().sum():,}')
    b.metric("Observed fraud cases", f'{metrics["fraud_count"]:,}')
    c.metric("Label coverage", f"{coverage:.1%}")
    st.caption("Unknown labels stay unknown. Rates are calculated across all labeled transactions, including error rows, within the selected scope.")
    group = st.selectbox("Compare by", ["merchant_category", "use_chip", "card_type", "merchant_state"])
    minimum = st.number_input("Minimum labeled transactions per group", min_value=1, value=30, step=10)
    grouped = risk_by_group(scope, group, int(minimum))
    if grouped.empty:
        st.info("No group meets the minimum labeled sample size.")
    else:
        plot = grouped.copy()
        plot["rate_pct"] = plot["rate"].astype(float) * 100
        plot["plus"] = (plot["ci_high"] - plot["rate"].astype(float)) * 100
        plot["minus"] = (plot["rate"].astype(float) - plot["ci_low"]) * 100
        fig = px.bar(plot, x=group, y="rate_pct", error_y="plus", error_y_minus="minus",
                     color_discrete_sequence=[PALETTE[1]], hover_data=["labeled", "fraud"])
        fig.update_layout(xaxis_title=None, yaxis_title="Observed fraud rate · %")
        chart(polish(fig), "risk")
        table(grouped, column_config={col: st.column_config.NumberColumn(format="%.4f") for col in ["rate", "ci_low", "ci_high"]})
        download(grouped, "Download risk comparison", "fraud_patterns.csv", "risk_csv")
    st.warning("These are exploratory associations, not fraud predictions or causal effects. Wilson 95% intervals assume independent observations; repeated customers and incomplete labels can make uncertainty larger.")

with actions:
    st.subheader("From a segment to a testable action")
    st.caption("Candidate lists are hypotheses for a controlled pilot, not credit approvals or proven financial impact.")
    a, b = st.columns(2)
    with a:
        st.markdown("#### Re-engage valuable inactive customers")
        st.metric("At-risk candidates", f"{len(retention):,}")
        st.write("Offer a relevant reactivation message to customers with low recency scores and historically stronger frequency or spending within the lookback window.")
        st.caption("Pilot: randomize eligible customers into treatment/control. Primary metric: 30-day reactivation rate. Track incentive cost and opt-outs.")
        out = retention[["client_id", "Recency", "Frequency", "Monetary"]]
        table(out.head(15))
        download(out, "Download retention candidates", "retention_candidates.csv", "retention_csv")
    with b:
        st.markdown("#### Explore a credit-card proposition")
        st.metric("Discovery candidates", f"{len(cross_sell):,}")
        st.write("Select active customers in the top spending quartile who have no Credit card in the supplied card registry.")
        st.caption("Pilot: validate existing ownership, consent and underwriting eligibility separately. Compare application completion and incremental contribution after costs.")
        out = cross_sell[["client_id", "Frequency", "Monetary", "has_credit_card"]]
        table(out.head(15))
        download(out, "Download discovery candidates", "cross_sell_candidates.csv", "cross_sell_csv")
    st.info("No uplift, savings or revenue improvement is claimed: no campaign experiment has been run. Spending projections have not been labeled as customer lifetime value.")

with quality:
    st.subheader("Data quality is part of the result")
    st.caption("Checks below describe the entire loaded dataset, before dashboard filters.")
    table(bundle.quality)
    missing_users = raw.loc[raw["user_match"].ne("both"), "client_id"].nunique()
    st.write(f"Registry: {len(bundle.users):,} customers. No transaction history: {(~bundle.users['id'].isin(raw['client_id'])).sum():,}. Unmatched transaction customer IDs: {missing_users:,}.")
    st.markdown("""
**Metric contract**
- Net value sums error-free transaction amounts; negative amounts are refunds/reversals.
- Purchase metrics and RFM use positive, error-free transactions.
- Fraud rate = positive labels / known labels. Missing labels never become zero.
- RFM scores use average ranks; recency is reversed. At-risk rules run before loyal rules.
- Customer age, debt and income are source snapshot attributes, not historical facts.
- Charts and candidate lists are descriptive; dataset sampling can alter scores and rankings.
""")
    st.markdown("**Reproducibility:** one deterministic demo generator, one shared Python pipeline, executable SQLite queries, automated analytical and UI tests. See README and docs/METHODOLOGY.md.")
    download(bundle.quality, "Download data quality checks", "data_quality.csv", "quality_csv")

st.divider()
st.caption("LedgerLens · Transaction analytics portfolio · Synthetic demo by default · Source and methodology documented in the repository")

