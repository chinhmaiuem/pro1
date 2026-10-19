"""Reproducible fictional data. No customer/card identifiers from the original files."""
import argparse
from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.data_loader import ROOT


def generate(directory, seed=42):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    count = 240
    ids = np.arange(1, count + 1)
    users = pd.DataFrame({
        "id": ids, "current_age": rng.integers(20, 78, count),
        "yearly_income": rng.integers(25000, 150000, count),
        "total_debt": rng.integers(0, 80000, count), "credit_score": rng.integers(550, 840, count),
    })
    cards = pd.DataFrame({
        "id": ids * 10, "client_id": ids,
        "card_type": np.where(ids % 3 == 0, "Credit", "Debit"),
        "card_brand": np.where(ids % 2 == 0, "Visa", "Mastercard"),
    })
    mcc = pd.DataFrame({
        "mcc_code": [5411, 5812, 5541, 5311, 4511, 5732],
        "merchant_category": ["Groceries", "Restaurants", "Fuel", "Retail", "Travel", "Electronics"],
    })
    # Client 240 intentionally has no activity; 1..30 stop purchasing mid-2019.
    weights = rng.lognormal(0, 1.1, count - 1)
    client = rng.choice(ids[:-1], size=6000, p=weights / weights.sum())
    days = rng.integers(0, 730, len(client))
    days = np.where(client <= 30, np.minimum(days, 500), days)
    dates = pd.Timestamp("2018-01-01") + pd.to_timedelta(days, unit="D") + pd.to_timedelta(rng.integers(0, 24, len(client)), unit="h")
    amounts = np.round(rng.lognormal(3.8, 1.0, len(client)) * (1 + client % 7 / 5), 2)
    amounts[rng.random(len(client)) < 0.025] *= -1
    methods = rng.choice(["Chip Transaction", "Swipe Transaction", "Online Transaction"], len(client), p=[0.55, 0.25, 0.20])
    codes = rng.choice(mcc["mcc_code"], len(client))
    trans = pd.DataFrame({
        "id": np.arange(1, len(client)+1), "client_id": client, "card_id": client*10,
        "date": dates, "amount": amounts, "mcc": codes, "use_chip": methods,
        "merchant_state": rng.choice(["CA", "NY", "TX", "FL"], len(client)),
        "errors": np.where(rng.random(len(client)) < 0.012, "Technical error", ""),
    }).sort_values("id")
    # Artificial probabilities serve UI testing, never evidence of real-world risk.
    probability = 0.006 + 0.025 * (methods == "Online Transaction") + 0.008 * (codes == 5732)
    fraud = rng.random(len(client)) < probability
    labels = pd.DataFrame({"id": trans["id"], "label": np.where(fraud, "Yes", "No")})
    labels = labels.loc[rng.random(len(labels)) > 0.06]
    for name, frame in {
        "users_data.csv": users, "cards_data.csv": cards, "mcc_codes.csv": mcc,
        "transactions_data.csv": trans, "train_fraud_labels.csv": labels,
    }.items():
        frame.to_csv(directory / name, index=False, lineterminator="\n")
    return directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "demo")
    args = parser.parse_args()
    print(generate(args.output))
