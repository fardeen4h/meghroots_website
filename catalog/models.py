from django.db import models # pyright: ignore[reportMissingModuleSource]
from django.urls import reverse # pyright: ignore[reportMissingModuleSource]
from django.utils.text import slugify # type: ignore
from urllib.parse import urlparse
from django.core.exceptions import ValidationError # pyright: ignore[reportMissingModuleSource]

def validate_amazon_url(value):
    host = (urlparse(value).hostname or "").lower()
    allowed = ("amazon.in", "www.amazon.in", "amzn.in", "amzn.to", "a.co")
    if host not in allowed:
        raise ValidationError(
            "Enter an Amazon India link (amazon.in, amzn.in or amzn.to)."
        )
    
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, blank=True)
    tagline = models.CharField(max_length=200, blank=True)
    story = models.TextField(blank=True, help_text="Origin story: village, farmers, harvest, etc.")
    description = models.TextField()
    image = models.ImageField(upload_to="products/")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalog:product_detail", args=[self.slug])

    @property
    def starting_price(self):
        v = self.variants.filter(is_active=True).order_by("price").first()
        return v.price if v else None

    def __str__(self):
        return self.name


class Variant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    label = models.CharField(max_length=50, help_text="e.g. 250g pouch")
    sku = models.CharField(max_length=40, unique=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    weight_grams = models.PositiveIntegerField(help_text="Needed later for shipping cost")
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    amazon_url = models.URLField(
        blank=True,
        validators=[validate_amazon_url], # pyright: ignore[reportUndefinedVariable]
        help_text="Optional. Amazon India listing for this pack size.",
    )
    class Meta:
        ordering = ["weight_grams"]
        unique_together = ("product", "label")

    def __str__(self):
        return f"{self.product.name} - {self.label}"