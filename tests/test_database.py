"""Database connection and data tests."""
import unittest

from database import connection, repository
from tests.helpers import ANCHOR, DemoDataTestCase


class DatabaseTests(DemoDataTestCase):
    def test_connection_works(self):
        result = connection.test_connection()
        self.assertTrue(result["ok"], result)

    def test_tables_have_expected_sizes(self):
        counts = repository.get_table_counts()
        self.assertEqual(counts["products"], 22)
        self.assertEqual(counts["customers"], 60)
        self.assertGreater(counts["sales"], 1000)

    def test_reference_date_is_latest_sale(self):
        self.assertEqual(repository.get_reference_date(), ANCHOR)

    def test_sales_dataframe_has_calculated_columns(self):
        df = repository.get_sales_df()
        for column in ("profit", "month", "product_name", "customer_name", "region"):
            self.assertIn(column, df.columns)
        self.assertGreater(df["profit"].sum(), 0)

    def test_date_filter_is_inclusive(self):
        df = repository.get_sales_df(ANCHOR, ANCHOR)
        self.assertGreaterEqual(len(df), 1)
        self.assertTrue((df["sale_date"].dt.date == ANCHOR).all())

    def test_only_select_queries_allowed(self):
        with self.assertRaises(connection.DatabaseError):
            connection.run_query("DELETE FROM sales")
        with self.assertRaises(connection.DatabaseError):
            connection.run_query("DROP TABLE sales")

    def test_sample_csv_files_created(self):
        from config import settings
        for name in ("sales.csv", "products.csv", "customers.csv", "crm_contacts.csv"):
            self.assertTrue((settings.SAMPLE_DATA_DIR / name).exists(), name)


if __name__ == "__main__":
    unittest.main()
