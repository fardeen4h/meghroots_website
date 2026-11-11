from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from cart.cart import Cart
from catalog.models import Variant
from .forms import CheckoutForm
from .models import Order, OrderItem
from .shipping import calculate_shipping


class OutOfStock(Exception):
    pass


def _summary(cart):
    items = list(cart)
    subtotal = sum((i["total"] for i in items), Decimal("0.00"))
    weight = sum(i["variant"].weight_grams * i["quantity"] for i in items)
    shipping = calculate_shipping(subtotal, weight)
    return items, subtotal, shipping, subtotal + shipping


def _create_order(form, items, subtotal, shipping, total):
    with transaction.atomic():
        # Lock the variant rows so two buyers can't take the same last unit
        ids = [i["variant"].id for i in items]
        locked = {
            v.id: v
            for v in Variant.objects.select_for_update(of=("self",)).filter(id__in=ids)
        }

        for item in items:
            v = locked.get(item["variant"].id)
            if v is None or v.stock < item["quantity"]:
                raise OutOfStock(
                    f"Sorry, there isn't enough stock of {item['variant']} for your order. "
                    "Please adjust your cart."
                )

        order = form.save(commit=False)
        order.payment_method = Order.PaymentMethod.COD
        order.payment_status = Order.PaymentStatus.PENDING
        order.status = Order.Status.PLACED
        order.subtotal = subtotal
        order.shipping_cost = shipping
        order.total = total
        order.save()

        for item in items:
            v = locked[item["variant"].id]
            OrderItem.objects.create(
                order=order,
                variant=v,
                product_name=v.product.name,
                variant_label=v.label,
                sku=v.sku,
                unit_price=item["price"],
                quantity=item["quantity"],
                line_total=item["total"],
            )
            v.stock -= item["quantity"]
            v.save(update_fields=["stock"])

    return order


def checkout(request):
    cart = Cart(request)
    items, subtotal, shipping, total = _summary(cart)

    if not items:
        messages.error(request, "Your cart is empty.")
        return redirect("cart:detail")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                order = _create_order(form, items, subtotal, shipping, total)
            except OutOfStock as exc:
                messages.error(request, str(exc))
                return redirect("cart:detail")
            cart.clear()
            return redirect("orders:confirmation", token=order.access_token)
    else:
        form = CheckoutForm()

    return render(request, "orders/checkout.html", {
        "form": form,
        "items": items,
        "subtotal": subtotal,
        "shipping": shipping,
        "total": total,
    })


def confirmation(request, token):
    order = get_object_or_404(
        Order.objects.prefetch_related("items"), access_token=token
    )
    return render(request, "orders/confirmation.html", {"order": order})
