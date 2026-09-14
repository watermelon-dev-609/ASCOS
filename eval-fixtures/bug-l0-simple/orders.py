"""Simplified checkout total calculation."""


def calculate_total(items, coupon=None):
    """Return the payable total for a cart.

    Args:
        items: list of {"price": float, "qty": int}
        coupon: optional {"code": str, "amount": float} - fixed amount off

    Returns:
        The payable total rounded to 2 decimals.
    """
    subtotal = sum(item["price"] * item["qty"] for item in items)

    discount_rate = 0.0
    if coupon:
        discount_rate = coupon["amount"] / subtotal

    return round(subtotal * (1 - discount_rate), 2)
