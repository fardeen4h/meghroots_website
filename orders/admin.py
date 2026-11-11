from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = (
        "variant", "product_name", "variant_label", "sku",
        "unit_price", "quantity", "line_total",
    )

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number", "created_at", "full_name", "phone", "state",
        "total", "payment_method", "payment_status", "status",
    )
    list_filter = ("status", "payment_method", "payment_status", "state")
    search_fields = ("full_name", "phone", "email")
    readonly_fields = (
        "access_token", "subtotal", "shipping_cost", "total", "created_at", "updated_at",
    )
    inlines = [OrderItemInline]
