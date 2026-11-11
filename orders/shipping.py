from decimal import Decimal

# PLACEHOLDER RATES: replace with your real courier costs.
FREE_SHIPPING_ABOVE = Decimal("999")    # free shipping when subtotal is at least this
BASE_RATE = Decimal("60")               # covers the first 500 g
PER_EXTRA_500G = Decimal("40")          # each additional 500 g (or part of it)


def calculate_shipping(subtotal, weight_grams):
    if subtotal >= FREE_SHIPPING_ABOVE:
        return Decimal("0.00")
    slabs = -(-weight_grams // 500)     # ceiling division
    extra = max(0, slabs - 1)
    return BASE_RATE + PER_EXTRA_500G * extra
