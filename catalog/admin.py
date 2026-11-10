from django.contrib import admin # pyright: ignore[reportMissingModuleSource]
from .models import Category, Product, Variant


class VariantInline(admin.TabularInline):
    model = Variant
    extra = 3


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    inlines = [VariantInline]