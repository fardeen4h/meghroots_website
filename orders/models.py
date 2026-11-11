import uuid

from django.core.validators import RegexValidator
from django.db import models

from catalog.models import Variant

INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa",
    "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala",
    "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland",
    "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Andaman and Nicobar Islands", "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu", "Delhi", "Jammu and Kashmir",
    "Ladakh", "Lakshadweep", "Puducherry",
]
STATE_CHOICES = [(s, s) for s in INDIAN_STATES]

phone_validator = RegexValidator(
    r"^[6-9]\d{9}$", "Enter a valid 10-digit Indian mobile number."
)
pincode_validator = RegexValidator(r"^\d{6}$", "Enter a valid 6-digit PIN code.")


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING_PAYMENT = "pending_payment", "Pending payment"
        PLACED = "placed", "Placed"
        PACKED = "packed", "Packed"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    class PaymentMethod(models.TextChoices):
        COD = "cod", "Cash on delivery"
        ONLINE = "online", "Online payment"

    class PaymentStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"

    # Public, unguessable key used in the confirmation URL
    access_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Customer and delivery details
    full_name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=10, validators=[phone_validator])
    address_line1 = models.CharField("Address line 1", max_length=200)
    address_line2 = models.CharField("Address line 2 (optional)", max_length=200, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=60, choices=STATE_CHOICES)
    pincode = models.CharField("PIN code", max_length=6, validators=[pincode_validator])
    notes = models.TextField("Delivery notes (optional)", blank=True)

    # Status
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLACED)
    payment_method = models.CharField(
        max_length=10, choices=PaymentMethod.choices, default=PaymentMethod.COD
    )
    payment_status = models.CharField(
        max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.PENDING
    )

    # Money
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def order_number(self):
        return f"MR{self.pk:05d}" if self.pk else ""

    def __str__(self):
        return f"{self.order_number} - {self.full_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(Variant, on_delete=models.SET_NULL, null=True, blank=True)

    # Snapshot at time of purchase
    product_name = models.CharField(max_length=150)
    variant_label = models.CharField(max_length=50)
    sku = models.CharField(max_length=40)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField()
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product_name} ({self.variant_label}) x {self.quantity}"
