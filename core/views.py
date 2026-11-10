from django.shortcuts import render # pyright: ignore[reportMissingModuleSource]
from catalog.models import Product


def home(request):
    products = Product.objects.filter(is_active=True).prefetch_related("variants")[:6]
    return render(request, "core/home.html", {"products": products})


def about(request):
    return render(request, "core/about.html")


def contact(request):
    return render(request, "core/contact.html")