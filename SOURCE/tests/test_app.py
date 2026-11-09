"""HTTP contract and database failure tests; no live database is required."""

from datetime import datetime
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import MagicMock

import pymysql

APP_PATH = Path(__file__).resolve().parents[1] / "app" / "app.py"
SPEC = importlib.util.spec_from_file_location("group08_orders_app", APP_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class OrdersAppTests(unittest.TestCase):
    def setUp(self):
        self.connection = MagicMock()
        self.cursor = self.connection.cursor.return_value.__enter__.return_value
        self.connector = MagicMock(return_value=self.connection)
        self.app = MODULE.create_app({"TESTING": True, "DB_CONNECTOR": self.connector})
        # Dynamic import has no importable module path for Flask root discovery.
        self.app.root_path = str(APP_PATH.parent)
        self.client = self.app.test_client()
        self.payload = dict(customer_alias="LAB-DEMO", product_name="Notebook", quantity=2, unit_price_vnd=25000)
        self.row = dict(id=101, **self.payload, created_at_utc=datetime(2026, 11, 8, 0, 0, 0, 123456))

    def test_home_is_accessible_without_db_and_uses_local_assets(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Tạo đơn hàng giả", response.get_data(as_text=True))
        self.assertIn("script-src 'self'", response.headers["Content-Security-Policy"])
        self.connector.assert_not_called()

    def test_health_reads_actual_orders_table(self):
        self.cursor.fetchone.return_value = {"total": 100}
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "ok", "database": "ok", "orders_count": 100})
        self.cursor.execute.assert_called_once_with("SELECT COUNT(*) AS total FROM orders")
        self.connection.close.assert_called_once()

    def test_health_db_failure_is_503_without_error_details(self):
        self.connector.side_effect = pymysql.OperationalError(1045, "sensitive-credential-details")
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json, {"status": "unavailable", "database": "unavailable"})
        self.assertNotIn("sensitive", response.get_data(as_text=True))

    def test_order_list_has_total_and_utc_timestamp(self):
        self.cursor.fetchone.return_value = {"total": 101}
        self.cursor.fetchall.return_value = [self.row]
        response = self.client.get("/api/orders")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["total"], 101)
        self.assertEqual(response.json["orders"][0]["created_at_utc"], "2026-11-08T00:00:00.123456Z")
        self.assertIn("ORDER BY id DESC LIMIT 100", self.cursor.execute.call_args_list[1].args[0])
        self.connection.close.assert_called_once()

    def test_create_uses_parameters_and_commits_before_success(self):
        self.cursor.lastrowid = 101
        self.cursor.fetchone.return_value = self.row
        response = self.client.post("/api/orders", json=self.payload, headers={"Origin": "http://localhost"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["order"]["id"], 101)
        sql, values = self.cursor.execute.call_args_list[0].args
        self.assertNotIn("LAB-DEMO", sql)
        self.assertEqual(values, ("LAB-DEMO", "Notebook", 2, 25000))
        self.assertEqual(self.cursor.execute.call_args_list[1].args[1], (101,))
        self.connection.commit.assert_called_once()
        self.connection.close.assert_called_once()

    def test_insert_failure_closes_connection_without_commit(self):
        self.cursor.execute.side_effect = pymysql.OperationalError(2006, "secret-host")
        response = self.client.post("/api/orders", json=self.payload)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("secret-host", response.get_data(as_text=True))
        self.connection.commit.assert_not_called()
        self.connection.close.assert_called_once()

    def test_commit_failure_does_not_claim_creation(self):
        self.cursor.lastrowid = 101
        self.cursor.fetchone.return_value = self.row
        self.connection.commit.side_effect = pymysql.OperationalError(2013, "lost connection")
        response = self.client.post("/api/orders", json=self.payload)
        self.assertEqual(response.status_code, 503)
        self.connection.close.assert_called_once()

    def test_list_failure_hides_database_details(self):
        self.connector.side_effect = pymysql.OperationalError(1049, "internal-db-name")
        response = self.client.get("/api/orders")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("internal-db-name", response.get_data(as_text=True))

    def test_invalid_order_fields_never_connect_to_database(self):
        cases = [
            {"customer_alias": "Alice Smith"},
            {"customer_alias": "LAB-X'; DROP TABLE orders;--"},
            {"product_name": "arbitrary-product"},
            {"quantity": True}, {"quantity": 0}, {"quantity": 101},
            {"quantity": 1.5}, {"quantity": "2"},
            {"unit_price_vnd": False}, {"unit_price_vnd": 0},
            {"unit_price_vnd": 100000001}, {"unit_price_vnd": 1.5},
        ]
        for changes in cases:
            with self.subTest(changes=changes):
                response = self.client.post("/api/orders", json=self.payload | changes)
                self.assertEqual(response.status_code, 400)
        self.connector.assert_not_called()

    def test_json_shape_and_malformed_json_are_400(self):
        for value in ([], "text", True, 42, {}, self.payload | {"extra": "field"}):
            with self.subTest(value=value):
                self.assertEqual(self.client.post("/api/orders", json=value).status_code, 400)
        for data in ("null", "{"):
            self.assertEqual(self.client.post("/api/orders", data=data, content_type="application/json").status_code, 400)
        self.connector.assert_not_called()

    def test_form_submission_is_not_accepted_as_json(self):
        self.assertEqual(self.client.post("/api/orders", data=self.payload).status_code, 415)
        self.connector.assert_not_called()

    def test_cross_origin_and_cross_site_writes_are_rejected(self):
        for headers in ({"Origin": "http://evil.test"}, {"Origin": "null"}, {"Sec-Fetch-Site": "cross-site"}):
            with self.subTest(headers=headers):
                self.assertEqual(self.client.post("/api/orders", json=self.payload, headers=headers).status_code, 403)
        self.connector.assert_not_called()

    def test_untrusted_host_is_rejected(self):
        self.assertEqual(self.client.get("/health", headers={"Host": "evil.test"}).status_code, 400)
        self.connector.assert_not_called()

    def test_large_payload_is_413_json(self):
        response = self.client.post("/api/orders", data='{"padding":"' + "x" * 9000 + '"}', content_type="application/json")
        self.assertEqual(response.status_code, 413)
        self.assertIsNotNone(response.json)
        self.connector.assert_not_called()


if __name__ == "__main__":
    unittest.main()
