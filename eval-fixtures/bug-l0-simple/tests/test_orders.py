import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orders import calculate_total


class TestCalculateTotal(unittest.TestCase):
    def test_single_item(self):
        self.assertEqual(calculate_total([{"price": 10.0, "qty": 2}]), 20.0)

    def test_multiple_items(self):
        items = [{"price": 10.0, "qty": 2}, {"price": 2.5, "qty": 4}]
        self.assertEqual(calculate_total(items), 30.0)

    def test_coupon_applies_fixed_amount_off(self):
        items = [{"price": 100.0, "qty": 1}]
        self.assertEqual(calculate_total(items, {"code": "SAVE20", "amount": 20.0}), 80.0)

    def test_coupon_larger_than_subtotal_does_not_go_negative(self):
        # This is the documented behaviour we currently assert; it is NOT the bug.
        items = [{"price": 10.0, "qty": 1}]
        self.assertEqual(calculate_total(items, {"code": "BIG", "amount": 15.0}), -5.0)


if __name__ == "__main__":
    unittest.main()
