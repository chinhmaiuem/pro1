"""Validated CSV ingestion. Pure pandas functions; no UI or cache state."""
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TRANSACTION_FILES = ("transactions_data.csv", "transactions_data_25pc.csv", "transactions_data_10pc.csv")
REQUIRED = {
    "users": {"id", "current_age", "yearly_income", "total_debt", "credit_score"},
    "cards": {"id", "client_id", "card_type", "card_brand"},
    "transactions": {"id", "client_id", "card_id", "date", "amount", "mcc", "use_chip"},
    "mcc": {"mcc_code", "merchant_category"},
    "labels": {"id", "label"},
}


class DataValidationError(ValueError):
    """An input violates the documented data contract."""


@dataclass
class AnalysisData:
    transactions: pd.DataFrame
    users: pd.DataFrame
    cards: pd.DataFrame
    quality: pd.DataFrame
    source: str


def source_files(directory):
    directory = Path(directory)
    candidates = [directory / name for name in TRANSACTION_FILES if (directory / name).is_file()]
    if len(candidates) != 1:
        raise DataValidationError(
            "Keep exactly one transaction CSV in the data folder: " + ", ".join(TRANSACTION_FILES)
        )
    paths = {"transactions": candidates[0]}
    for key, name in (("users", "users_data.csv"), ("cards", "cards_data.csv"), ("mcc", "mcc_codes.csv")):
        paths[key] = directory / name
        if not paths[key].is_file():
            raise DataValidationError(f"Missing file: {name}")
    label_path = directory / "train_fraud_labels.csv"
    if label_path.is_file():
        paths["labels"] = label_path
    return paths


def file_signature(directory):
    """Include file identity/size/mtime in the Streamlit cache key."""
    return tuple((key, str(p.resolve()), p.stat().st_size, p.stat().st_mtime_ns)
                 for key, p in sorted(source_files(directory).items()))


def money(series, name):
    cleaned = series.astype("string").str.replace(r"[$,]", "", regex=True).str.strip()
    values = pd.to_numeric(cleaned, errors="coerce").astype(float)
    if values.isna().any() or not np.isfinite(values).all():
        raise DataValidationError(f"{name}: missing or invalid numeric value")
    return values


def integer(series, name):
    values = pd.to_numeric(series, errors="coerce")
    if values.isna().any() or not np.isfinite(values).all() or (values % 1 != 0).any():
        raise DataValidationError(f"{name}: expected non-missing integer IDs")
    return values.astype("int64")


def normalize_labels(series):
    mapping = {"yes": 1, "no": 0, "1": 1, "0": 0, "1.0": 1, "0.0": 0}
    cleaned = series.astype("string").str.strip().str.lower().replace("", pd.NA)
    invalid = cleaned.notna() & ~cleaned.isin(mapping)
    if invalid.any():
        raise DataValidationError("labels.label: expected Yes/No, 1/0 or missing")
    return cleaned.map(mapping).astype("Int8")


def prepare_tables(tables, source="custom"):
    """Validate keys before joins; preserve unknown labels and transaction row count."""
    data = {key: frame.copy() for key, frame in tables.items()}
    data.setdefault("labels", pd.DataFrame(columns=["id", "label"]))
    for key, columns in REQUIRED.items():
        if key not in data:
            raise DataValidationError(f"Missing table: {key}")
        missing = columns - set(data[key].columns)
        if missing:
            raise DataValidationError(f"{key}: missing columns {sorted(missing)}")
        pk = "mcc_code" if key == "mcc" else "id"
        data[key][pk] = integer(data[key][pk], f"{key}.{pk}")
        if data[key][pk].duplicated().any():
            raise DataValidationError(f"{key}.{pk}: duplicate primary keys")

    trans, users, cards, mcc, labels = (data[k] for k in ("transactions", "users", "cards", "mcc", "labels"))
    if trans.empty:
        raise DataValidationError("transactions: the input is empty")
    for key in ("client_id", "card_id", "mcc"):
        trans[key] = integer(trans[key], f"transactions.{key}")
    cards["client_id"] = integer(cards["client_id"], "cards.client_id")
    trans["date"] = pd.to_datetime(trans["date"], errors="coerce", format="mixed")
    if trans["date"].isna().any():
        raise DataValidationError("transactions.date: invalid or missing date")
    if not pd.api.types.is_datetime64_any_dtype(trans["date"]) or trans["date"].dt.tz is not None:
        raise DataValidationError("transactions.date: normalize to timezone-naive timestamps before import")
    trans["amount"] = money(trans["amount"], "transactions.amount")
    for col in ("yearly_income", "total_debt", "current_age", "credit_score"):
        users[col] = money(users[col], f"users.{col}")
    if ((users["current_age"] < 0) | (users["current_age"] > 120)).any():
        raise DataValidationError("users.current_age: expected 0..120")
    users["debt_to_income"] = users["total_debt"].div(users["yearly_income"].where(users["yearly_income"] > 0))
    users["age_group"] = pd.cut(users["current_age"], [0, 25, 35, 45, 55, 65, 120],
                                labels=["0–25", "26–35", "36–45", "46–55", "56–65", "66+"], include_lowest=True)
    labels["is_fraud"] = normalize_labels(labels["label"])
    if "errors" in trans:
        error_text = trans["errors"].astype("string").fillna("").str.strip().str.lower()
        trans["has_error"] = ~error_text.isin(["", "no error", "none", "nan"])
    else:
        trans["has_error"] = False
    trans["is_purchase"] = trans["amount"].gt(0) & ~trans["has_error"]

    # Only analytical fields enter the app, never card numbers, CVV or addresses.
    users = users[["id", "current_age", "age_group", "yearly_income", "total_debt", "credit_score", "debt_to_income"]].copy()
    cards = cards[["id", "client_id", "card_type", "card_brand"]].copy()
    merged = trans.merge(labels[["id", "is_fraud"]], on="id", how="left", validate="one_to_one")
    merged = merged.merge(cards.rename(columns={"id": "card_id"}), on=["card_id", "client_id"],
                          how="left", validate="many_to_one", indicator="card_match")
    merged = merged.merge(users.rename(columns={"id": "client_id"}), on="client_id", how="left",
                          validate="many_to_one", indicator="user_match")
    merged = merged.merge(mcc, left_on="mcc", right_on="mcc_code", how="left",
                          validate="many_to_one", indicator="mcc_match")
    merged["merchant_category"] = merged["merchant_category"].fillna("Unknown category")
    merged["card_type"] = merged["card_type"].fillna("Unknown card")
    merged["card_brand"] = merged["card_brand"].fillna("Unknown brand")
    for column in ("merchant_state", "merchant_city"):
        if column not in merged:
            merged[column] = "Unknown"
        merged[column] = merged[column].fillna("Unknown")
    merged["year"] = merged["date"].dt.year
    merged["month"] = merged["date"].dt.to_period("M").astype(str)

    checks = []
    def check(name, count, detail, warn=True):
        checks.append({"check": name, "count": int(count), "status": "Review" if count and warn else "Pass", "detail": detail})
    check("Transaction row preservation", len(merged) - len(trans), "Joins must not duplicate or drop transactions")
    for name in ("card", "user", "mcc"):
        check(f"Unmatched {name} references", merged[f"{name}_match"].ne("both").sum(), "Retained and reported; investigate source keys")
    check("Unlabeled transactions", merged["is_fraud"].isna().sum(), "Excluded from fraud-rate denominator")
    check("Unused label IDs", (~labels["id"].isin(trans["id"])).sum(), "May be expected for a transaction sample")
    check("Refund / reversal rows", trans["amount"].lt(0).sum(), "Included in net value; excluded from purchase RFM", False)
    check("Rows with transaction errors", trans["has_error"].sum(), "Excluded from settled value and purchase RFM", False)
    check("Nonpositive income", users["yearly_income"].le(0).sum(), "Debt-to-income left unknown")
    return AnalysisData(merged, users, cards, pd.DataFrame(checks), source)


def load_data(directory):
    paths = source_files(directory)
    tables = {}
    for key, path in paths.items():
        optional = {"transactions": {"errors", "merchant_state", "merchant_city"}}
        allowed = REQUIRED[key] | optional.get(key, set())
        tables[key] = pd.read_csv(path, usecols=lambda name: name in allowed)
    return prepare_tables(tables, str(Path(directory).resolve()))

