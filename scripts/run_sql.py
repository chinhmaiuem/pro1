"""Run read-only portfolio analyses on a temporary in-memory SQLite database."""
import argparse
from pathlib import Path
import sqlite3
import sys
from contextlib import closing

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.data_loader import ROOT, load_data


def run_queries(bundle):
    with closing(sqlite3.connect(":memory:")) as connection:
        columns = ["id", "client_id", "card_id", "date", "amount", "is_purchase", "has_error",
                   "is_fraud", "merchant_category", "card_type"]
        transactions = bundle.transactions[columns].copy()
        transactions["date"] = transactions["date"].dt.strftime("%Y-%m-%d %H:%M:%S")
        transactions.to_sql("transactions", connection, index=False)
        bundle.users.to_sql("users", connection, index=False)
        bundle.cards.to_sql("cards", connection, index=False)
        return {path.stem: pd.read_sql_query(path.read_text(encoding="utf-8"), connection)
                for path in sorted((ROOT / "sql").glob("*.sql"))}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data" / "demo")
    args = parser.parse_args()
    for name, result in run_queries(load_data(args.data_dir)).items():
        print(f"\n{name}: {len(result)} rows")
        print(result.head(8).to_string(index=False))
