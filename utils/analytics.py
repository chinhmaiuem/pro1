"""Shared metrics used by dashboard, report and SQL parity checks."""
import numpy as np


def kpis(transactions):
    settled = transactions.loc[~transactions["has_error"]]
    purchases = transactions.loc[transactions["is_purchase"]]
    labeled = transactions["is_fraud"].dropna()
    return {
        "transactions": len(transactions),
        "customers": transactions["client_id"].nunique(),
        "purchase_value": float(purchases["amount"].sum()),
        "refund_value": float(-settled.loc[settled["amount"] < 0, "amount"].sum()),
        "net_value": float(settled["amount"].sum()),
        "avg_purchase": float(purchases["amount"].mean()) if len(purchases) else 0.0,
        "label_coverage": len(labeled) / len(transactions) if len(transactions) else 0.0,
        "fraud_rate": float(labeled.mean()) if len(labeled) else None,
        "fraud_count": int(labeled.sum()),
    }


def monthly_summary(transactions):
    df = transactions.loc[~transactions["has_error"]].copy()
    return df.groupby("month", as_index=False).agg(net_value=("amount", "sum"), transactions=("id", "count"))


def risk_by_group(transactions, group, min_labeled=30):
    """Labeled-only event rates with Wilson 95% intervals; not causal estimates."""
    valid = transactions.dropna(subset=["is_fraud"])
    result = valid.groupby(group, observed=True, dropna=False).agg(
        labeled=("id", "count"), fraud=("is_fraud", "sum")).reset_index()
    result = result.loc[result["labeled"] >= min_labeled].copy()
    result["rate"] = result["fraud"] / result["labeled"]
    n, p, z = result["labeled"], result["rate"].astype(float), 1.96
    center = (p + z*z/(2*n)) / (1 + z*z/n)
    half = z * np.sqrt(p*(1-p)/n + z*z/(4*n*n)) / (1 + z*z/n)
    result["ci_low"], result["ci_high"] = center - half, center + half
    return result.sort_values(["rate", "labeled"], ascending=False).reset_index(drop=True)


def segment_summary(profile):
    return profile.groupby("Segment", as_index=False).agg(
        customers=("client_id", "count"), purchase_value=("Monetary", "sum"),
        median_recency=("Recency", "median"), median_frequency=("Frequency", "median"))


def opportunity_lists(profile):
    active = profile.loc[profile["Frequency"] > 0]
    threshold = active["Monetary"].quantile(0.75) if len(active) else float("inf")
    retention = profile.loc[profile["Segment"].eq("At risk")].sort_values("Monetary", ascending=False)
    cross_sell = profile.loc[(~profile["has_credit_card"]) & profile["Monetary"].ge(threshold)
                             & profile["Frequency"].gt(0)].sort_values("Monetary", ascending=False)
    return retention, cross_sell


def safe_csv(frame):
    """Prevent spreadsheet formula interpretation in downloaded text cells."""
    result = frame.copy()
    for col in result.select_dtypes(include=["object", "string", "category"]).columns:
        result[col] = result[col].astype("string").map(
            lambda value: "'" + value if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")) else value)
    return result.to_csv(index=False).encode("utf-8-sig")
