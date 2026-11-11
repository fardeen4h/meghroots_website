from decimal import Decimal

from catalog.models import Variant

CART_SESSION_ID = "cart"
MAX_QTY_PER_ITEM = 20


class Cart:
    """Session-based cart: {variant_id: quantity}."""

    def __init__(self, request):
        self.session = request.session
        self.cart = self.session.setdefault(CART_SESSION_ID, {})

    def save(self):
        self.session.modified = True

    def add(self, variant, quantity=1, override=False):
        key = str(variant.id)
        current = self.cart.get(key, 0)
        new_qty = quantity if override else current + quantity
        new_qty = max(1, min(new_qty, variant.stock, MAX_QTY_PER_ITEM))
        self.cart[key] = new_qty
        self.save()

    def remove(self, variant_id):
        if str(variant_id) in self.cart:
            del self.cart[str(variant_id)]
            self.save()

    def clear(self):
        self.session[CART_SESSION_ID] = {}
        self.save()

    def __iter__(self):
        ids = [int(k) for k in self.cart.keys()]
        variants = (
            Variant.objects.filter(id__in=ids, is_active=True, product__is_active=True)
            .select_related("product")
        )
        found = {v.id: v for v in variants}

        # Drop anything that was deleted or deactivated since it was added
        for key in list(self.cart.keys()):
            if int(key) not in found:
                del self.cart[key]
                self.save()

        for variant_id, variant in found.items():
            quantity = self.cart[str(variant_id)]
            yield {
                "variant": variant,
                "quantity": quantity,
                "price": variant.price,
                "total": variant.price * quantity,
            }

    def __len__(self):
        return sum(self.cart.values())

    def get_total_price(self):
        return sum((item["total"] for item in self), Decimal("0.00"))

    def get_total_weight_grams(self):
        return sum(item["variant"].weight_grams * item["quantity"] for item in self)
