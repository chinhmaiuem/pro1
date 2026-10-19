"""Behavioral regression tests: joins, label denominators, RFM and SQL parity."""
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from scripts.generate_demo import generate
from scripts.run_sql import run_queries
from scripts.build_report import build_report
from utils.analytics import kpis, opportunity_lists, risk_by_group, safe_csv
from utils.data_loader import ROOT, DataValidationError, file_signature, load_data, normalize_labels, prepare_tables
from utils.segmentation import assign_rfm_segment, customer_profile, perform_rfm_segmentation, quintile_score

TEST_TMP = ROOT / "test-results"
TEST_TMP.mkdir(exist_ok=True)


def fixture():
    return {
        "users": pd.DataFrame({"id": [1, 2], "current_age": [30, 70], "yearly_income": ["$50,000", "$0"],
                              "total_debt": ["$5,000", "$10"], "credit_score": [720, 600]}),
        "cards": pd.DataFrame({"id": [10, 20], "client_id": [1, 2], "card_type": ["Debit", "Credit"], "card_brand": ["Visa", "Visa"]}),
        "mcc": pd.DataFrame({"mcc_code": [5411], "merchant_category": ["Groceries"]}),
        "transactions": pd.DataFrame({
            "id": [1, 2, 3, 4], "client_id": [1, 1, 1, 2], "card_id": [10, 10, 10, 20],
            "date": ["2019-12-01", "2019-12-02", "2019-12-03", "2019-12-04"],
            "amount": ["$100", "-$20", "$30", "$900"], "mcc": [5411]*4,
            "use_chip": ["Chip"]*4, "errors": ["", "", "", "Failed"],
        }),
        "labels": pd.DataFrame({"id": [1, 2], "label": [" YES ", "no"]}),
    }


class DataContractTests(unittest.TestCase):
    def test_missing_labels_remain_unknown_and_denominator_is_known_only(self):
        df = prepare_tables(fixture()).transactions
        self.assertEqual(df["is_fraud"].isna().sum(), 2)
        self.assertEqual(kpis(df)["fraud_rate"], 0.5)
        self.assertEqual(kpis(df)["label_coverage"], 0.5)

    def test_refunds_and_errors_have_separate_metric_semantics(self):
        metrics = kpis(prepare_tables(fixture()).transactions)
        self.assertEqual(metrics["purchase_value"], 130)
        self.assertEqual(metrics["refund_value"], 20)
        self.assertEqual(metrics["net_value"], 110)
        self.assertEqual(metrics["avg_purchase"], 65)

    def test_label_variants_and_invalid_labels(self):
        self.assertEqual(normalize_labels(pd.Series(["YES", " no ", "1.0", 0])).tolist(), [1, 0, 1, 0])
        with self.assertRaises(DataValidationError):
            normalize_labels(pd.Series(["maybe"]))

    def test_absent_label_file_still_supports_analysis(self):
        data = fixture()
        del data["labels"]
        result = prepare_tables(data)
        self.assertIsNone(kpis(result.transactions)["fraud_rate"])
        self.assertTrue(risk_by_group(result.transactions, "card_type").empty)

    def test_duplicate_keys_fail_before_join(self):
        for name in ("users", "cards", "mcc", "labels", "transactions"):
            with self.subTest(table=name):
                data = fixture()
                data[name] = pd.concat([data[name], data[name].iloc[[0]]], ignore_index=True)
                with self.assertRaises(DataValidationError):
                    prepare_tables(data)

    def test_wrong_card_owner_is_reported_not_joined(self):
        data = fixture()
        data["transactions"].loc[0, "card_id"] = 20
        result = prepare_tables(data)
        self.assertEqual(len(result.transactions), 4)
        self.assertEqual(result.transactions.iloc[0]["card_type"], "Unknown card")
        check = result.quality.set_index("check").loc["Unmatched card references"]
        self.assertEqual(check["count"], 1)

    def test_unknown_customers_and_categories_do_not_drop_rows(self):
        data = fixture()
        data["transactions"].loc[0, ["client_id", "mcc"]] = [999, 999]
        result = prepare_tables(data)
        self.assertEqual(len(result.transactions), 4)
        self.assertEqual(result.transactions.iloc[0]["merchant_category"], "Unknown category")
        self.assertEqual(result.quality.set_index("check").loc["Unmatched user references", "count"], 1)

    def test_invalid_dates_amounts_and_missing_columns_fail(self):
        for column, value in [("date", "not a date"), ("amount", "oops"), ("id", 1.5)]:
            with self.subTest(column=column):
                data = fixture()
                data["transactions"][column] = data["transactions"][column].astype(object)
                data["transactions"].loc[0, column] = value
                with self.assertRaises(DataValidationError):
                    prepare_tables(data)
        data = fixture()
        data["users"] = data["users"].drop(columns="credit_score")
        with self.assertRaises(DataValidationError):
            prepare_tables(data)

    def test_zero_income_does_not_create_infinity(self):
        result = prepare_tables(fixture())
        self.assertTrue(pd.isna(result.users.loc[result.users["id"].eq(2), "debt_to_income"].iloc[0]))

    def test_pii_is_not_read_into_analytical_tables(self):
        data = fixture()
        data["cards"]["cvv"] = "123"
        data["cards"]["card_number"] = "fictional"
        data["users"]["address"] = "fictional"
        bundle = prepare_tables(data)
        for frame in (bundle.cards, bundle.users, bundle.transactions):
            self.assertFalse({"cvv", "card_number", "address"} & set(frame.columns))

    def test_csv_formula_cells_are_escaped(self):
        result = safe_csv(pd.DataFrame({"text": ["=1+1", " @SUM(A1)", "normal"]})).decode("utf-8-sig")
        self.assertIn("'=1+1", result)
        self.assertIn("' @SUM(A1)", result)

    def test_changed_file_signature_and_optional_labels(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as tmp:
            generate(tmp)
            before = file_signature(tmp)
            label_file = Path(tmp) / "train_fraud_labels.csv"
            label_file.write_text("id,label\n1,Yes\n", encoding="utf-8")
            self.assertNotEqual(before, file_signature(tmp))
            label_file.unlink()
            self.assertEqual(load_data(tmp).transactions["is_fraud"].notna().sum(), 0)


class SegmentationTests(unittest.TestCase):
    def test_at_risk_takes_priority_over_historical_loyalty(self):
        self.assertEqual(assign_rfm_segment({"R_Score": 1, "F_Score": 5, "M_Score": 5}), "At risk")

    def test_tied_values_and_row_order_do_not_change_scores(self):
        series = pd.Series([0, 0, 5, 10, 10], index=[10, 11, 12, 13, 14])
        original = quintile_score(series)
        pd.testing.assert_series_equal(original.sort_index(), quintile_score(series.sample(frac=1, random_state=1)).sort_index())
        self.assertEqual(original.iloc[0], original.iloc[1])
        self.assertEqual(quintile_score(pd.Series([0, 0])).tolist(), [3, 3])
        self.assertGreater(quintile_score(series, reverse=True).iloc[0], quintile_score(series, reverse=True).iloc[-1])

    def test_window_is_inclusive_at_start_exclusive_at_end(self):
        transactions = pd.DataFrame({
            "id": [1, 2, 3, 4, 5], "client_id": [1]*5, "amount": [10]*5,
            "date": pd.to_datetime(["2019-12-01", "2019-12-02", "2019-12-31", "2020-01-01", "2019-12-30"]),
            "is_purchase": [True, True, True, True, False]})
        rfm = perform_rfm_segmentation(transactions, "2020-01-01", 30)
        self.assertEqual(rfm.iloc[0]["Frequency"], 2)
        self.assertEqual(rfm.iloc[0]["Monetary"], 20)
        self.assertEqual(rfm.iloc[0]["Recency"], 1)

    def test_no_purchases_and_registry_customers_are_supported(self):
        bundle = prepare_tables(fixture())
        bundle.transactions["is_purchase"] = False
        profile = customer_profile(bundle.transactions, bundle.users, bundle.cards)
        self.assertEqual(len(profile), 2)
        self.assertTrue(profile["Segment"].eq("No purchases in window").all())
        self.assertTrue(opportunity_lists(profile)[1].empty)

    def test_existing_credit_owners_are_never_cross_sell_candidates(self):
        bundle = load_data(ROOT / "data" / "demo")
        profile = customer_profile(bundle.transactions, bundle.users, bundle.cards)
        _, candidates = opportunity_lists(profile)
        self.assertFalse(candidates["has_credit_card"].any())
        self.assertTrue(profile.loc[profile.client_id.eq(240), "Segment"].eq("No purchases in window").all())


class SQLAndRiskTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = load_data(ROOT / "data" / "demo")
        cls.queries = run_queries(cls.bundle)

    def test_sql_monthly_metrics_match_python(self):
        result = self.queries["01_monthly_value"]
        self.assertAlmostEqual(result["net_value"].sum(), kpis(self.bundle.transactions)["net_value"])
        self.assertAlmostEqual(result.iloc[-1]["cumulative_net_value"], result["net_value"].sum())

    def test_findings_report_is_current(self):
        self.assertEqual((ROOT / "docs" / "DEMO_FINDINGS.md").read_text(encoding="utf-8"), build_report())

    def test_sql_rfm_matches_python_at_boundaries(self):
        py = customer_profile(self.bundle.transactions, self.bundle.users, self.bundle.cards).set_index("client_id").sort_index()
        sql = self.queries["03_customer_rfm"].set_index("client_id").sort_index()
        for sql_col, py_col in (("recency", "Recency"), ("frequency", "Frequency"), ("monetary", "Monetary")):
            pd.testing.assert_series_equal(sql[sql_col], py[py_col], check_dtype=False, check_names=False, atol=1e-7)

    def test_sql_fraud_rates_match_python(self):
        py = risk_by_group(self.bundle.transactions, "merchant_category").set_index("merchant_category").sort_index()
        sql = self.queries["02_fraud_rates"].set_index("merchant_category").sort_index()
        pd.testing.assert_series_equal(py["rate"], sql["fraud_rate"], check_dtype=False, check_names=False)

    def test_wilson_intervals_are_bounded_and_contain_point_estimates(self):
        result = risk_by_group(self.bundle.transactions, "merchant_category")
        self.assertTrue(result["ci_low"].between(0, 1).all())
        self.assertTrue(result["ci_high"].between(0, 1).all())
        self.assertTrue((result["ci_low"] <= result["rate"]).all())
        self.assertTrue((result["ci_high"] >= result["rate"]).all())
        self.assertTrue(risk_by_group(self.bundle.transactions, "merchant_category", 100000).empty)

    def test_sql_candidates_have_no_existing_credit_card(self):
        candidates = self.queries["04_cross_sell"]
        owners = set(self.bundle.cards.loc[self.bundle.cards.card_type.eq("Credit"), "client_id"])
        self.assertFalse(set(candidates["client_id"]) & owners)

    def test_demo_regeneration_is_byte_reproducible(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as tmp:
            generate(tmp)
            for path in (ROOT / "data" / "demo").glob("*.csv"):
                self.assertEqual(path.read_bytes(), (Path(tmp) / path.name).read_bytes())


if __name__ == "__main__":
    unittest.main()
