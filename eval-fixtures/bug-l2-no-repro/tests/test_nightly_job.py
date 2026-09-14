import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nightly_job import sweep


class FakeDb:
    """In-memory stand-in for the orders table."""

    def __init__(self, ids):
        self.rows = [{"id": i, "status": "pending"} for i in ids]

    def fetch_pending(self, limit, offset):
        pending = [r for r in self.rows if r["status"] == "pending"]
        return pending[offset:offset + limit]

    def update_status(self, order_id, status):
        for row in self.rows:
            if row["id"] == order_id:
                row["status"] = status


class TestSweep(unittest.TestCase):
    def test_moves_all_pending_orders(self):
        db = FakeDb(range(1, 11))
        self.assertEqual(sweep(db), 10)
        self.assertTrue(all(r["status"] == "processing" for r in db.rows))

    def test_leaves_non_pending_orders_alone(self):
        db = FakeDb(range(1, 6))
        db.update_status(3, "paid")
        self.assertEqual(sweep(db), 4)
        self.assertEqual(db.rows[2]["status"], "paid")

    def test_empty_table_is_a_noop(self):
        self.assertEqual(sweep(FakeDb([])), 0)


if __name__ == "__main__":
    unittest.main()
