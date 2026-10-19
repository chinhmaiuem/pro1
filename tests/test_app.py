"""Exercise the real Streamlit app, including reruns and empty states."""
import unittest
from streamlit.testing.v1 import AppTest
from utils.data_loader import ROOT


class DashboardTests(unittest.TestCase):
    def app(self):
        return AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()

    def test_demo_renders_all_tabs_and_exports(self):
        app = self.app()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.tabs), 5)
        self.assertGreaterEqual(len(app.get("plotly_chart")), 5)
        self.assertEqual(len(app.get("download_button")), 5)

    def test_empty_card_filter_is_a_clean_empty_state(self):
        app = self.app()
        app.multiselect(key="card_types").set_value([]).run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any("No transactions" in element.value for element in app.info))

    def test_period_card_and_rfm_filters_rerun_without_stale_tables(self):
        app = self.app()
        baseline = app.metric[0].value
        app.multiselect(key="card_types").set_value(["Credit"]).run()
        self.assertEqual(len(app.exception), 0)
        self.assertNotEqual(app.metric[0].value, baseline)
        app.selectbox(key="lookback").set_value(90).run()
        self.assertEqual(len(app.exception), 0)
        app.date_input[0].set_value(("2019-01-01", "2019-12-31")).run()
        self.assertEqual(len(app.exception), 0)

    def test_missing_local_dataset_has_actionable_error(self):
        app = self.app()
        app.selectbox(key="source").set_value("Local dataset").run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any("Cannot load" in element.value for element in app.error))

    def test_insufficient_risk_sample_is_a_clean_empty_state(self):
        app = self.app()
        app.number_input[0].set_value(100000).run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any("No group meets" in element.value for element in app.info))


if __name__ == "__main__":
    unittest.main()
