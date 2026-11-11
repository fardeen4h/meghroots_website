from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from catalog.models import Variant
from .cart import Cart


def _to_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def cart_detail(request):
    return render(request, "cart/detail.html", {"cart": Cart(request)})


@require_POST
def cart_add(request):
    variant = Variant.objects.filter(
        id=_to_int(request.POST.get("variant")),
        is_active=True,
        product__is_active=True,
    ).select_related("product").first()

    if variant is None:
        messages.error(request, "Please choose an available size.")
        return redirect("catalog:product_list")

    if variant.stock < 1:
        messages.error(request, f"Sorry, {variant} is out of stock.")
        return redirect(variant.product.get_absolute_url())

    quantity = max(1, _to_int(request.POST.get("quantity"), 1))
    Cart(request).add(variant, quantity)
    messages.success(request, f"Added {variant} to your cart.")
    return redirect("cart:detail")


@require_POST
def cart_update(request, variant_id):
    variant = get_object_or_404(Variant, id=variant_id, is_active=True)
    quantity = _to_int(request.POST.get("quantity"), 1)
    cart = Cart(request)
    if quantity < 1:
        cart.remove(variant.id)
    else:
        cart.add(variant, quantity, override=True)
    return redirect("cart:detail")


@require_POST
def cart_remove(request, variant_id):
    Cart(request).remove(variant_id)
    messages.success(request, "Item removed from your cart.")
    return redirect("cart:detail")
