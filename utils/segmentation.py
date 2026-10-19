"""Customer analysis with explicit windows and deterministic, tie-safe RFM rules."""
import pandas as pd


def quintile_score(series, reverse=False):
    """Equal values receive equal scores. Constant populations stay neutral."""
    if series.nunique() <= 1:
        return pd.Series(3, index=series.index, dtype="int64")
    percentile = (series.rank(method="average") - 1) / max(len(series) - 1, 1)
    score = (percentile * 5).astype(int).clip(upper=4) + 1
    return 6 - score if reverse else score


def assign_rfm_segment(row):
    r, f, m = row["R_Score"], row["F_Score"], row["M_Score"]
    if r <= 2:
        return "At risk" if f >= 3 or m >= 3 else "Hibernating"
    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    if f >= 4:
        return "Loyal"
    if m >= 4:
        return "High spenders"
    if r >= 4:
        return "Promising"
    return "Needs attention"


def perform_rfm_segmentation(transactions, reference_date=None, window_days=365):
    if window_days < 1:
        raise ValueError("window_days must be positive")
    if reference_date is None:
        reference_date = transactions["date"].max().normalize() + pd.Timedelta(days=1)
    reference_date = pd.Timestamp(reference_date)
    eligible = transactions.loc[
        transactions["is_purchase"] & (transactions["date"] < reference_date)
        & (transactions["date"] >= reference_date - pd.Timedelta(days=window_days))
    ].copy()
    rfm = eligible.groupby("client_id").agg(
        last_purchase=("date", "max"), Frequency=("id", "count"), Monetary=("amount", "sum"))
    rfm["Recency"] = (reference_date - rfm["last_purchase"]).dt.days
    for field, reverse in (("Recency", True), ("Frequency", False), ("Monetary", False)):
        rfm[field[0] + "_Score"] = quintile_score(rfm[field], reverse)
    rfm["RFM_Score"] = rfm[["R_Score", "F_Score", "M_Score"]].sum(axis=1)
    rfm["Segment"] = rfm.apply(assign_rfm_segment, axis=1) if not rfm.empty else pd.Series(dtype="str")
    return rfm.reset_index()


def customer_profile(transactions, users, cards, reference_date=None, window_days=365):
    rfm = perform_rfm_segmentation(transactions, reference_date, window_days)
    profile = users.rename(columns={"id": "client_id"}).merge(rfm, on="client_id", how="left", validate="one_to_one")
    profile["Segment"] = profile["Segment"].fillna("No purchases in window")
    profile[["Frequency", "Monetary"]] = profile[["Frequency", "Monetary"]].fillna(0)
    credit_owners = cards.loc[cards["card_type"].str.lower().eq("credit"), "client_id"]
    profile["has_credit_card"] = profile["client_id"].isin(credit_owners)
    profile["spend_share"] = profile["Monetary"] / max(profile["Monetary"].sum(), 1)
    return profile

