from django.urls import path # pyright: ignore[reportMissingModuleSource]
from . import views

app_name = "catalog"

urlpatterns = [
    path("shop/", views.product_list, name="product_list"),
    path("shop/<slug:category_slug>/", views.product_list, name="category"),
    path("product/<slug:slug>/", views.product_detail, name="product_detail"),
]