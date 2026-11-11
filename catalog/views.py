from django.shortcuts import get_object_or_404, render # pyright: ignore[reportMissingModuleSource]
from .models import Category, Product


def product_list(request, category_slug=None):
    products = Product.objects.filter(is_active=True).prefetch_related("variants")
    category = None
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    return render(request, "catalog/product_list.html", {
        "products": products,
        "category": category,
        "categories": Category.objects.all(),
    })


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.prefetch_related("variants"), slug=slug, is_active=True
    )
    variants = list(product.variants.filter(is_active=True))
    default_variant = next((v for v in variants if v.stock > 0), None)
    return render(request, "catalog/product_detail.html", {
        "product": product,
        "variants": variants,
        "default_variant": default_variant,
    })