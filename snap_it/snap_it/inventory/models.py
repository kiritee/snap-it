from django.db import models
from django.conf import settings
import uuid

class Inventory(models.Model):
    """Model representing a batch of items uploaded by a merchant."""
    inventory_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="inventories")
    inventory_name = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """Set inventory_name default if not provided."""
        if not self.inventory_name:
            self.inventory_name = f"Inventory-{self.created_at.strftime('%Y-%m-%d')}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.inventory_name} - {self.merchant.email}"


class Item(models.Model):
    """Model representing an item."""
    item_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item_name = models.CharField(max_length=255)
    item_description = models.TextField(blank=True, null=True)
    brand = models.CharField(max_length=100, blank=True, null=True)
    model_name = models.CharField(max_length=100, blank=True, null=True)
    model_number = models.CharField(max_length=100, blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    sub_category = models.CharField(max_length=100, blank=True, null=True)
    ean_number = models.CharField(max_length=13, blank=True, null=True)
    colour = models.CharField(max_length=50, blank=True, null=True)
    attribute1 = models.CharField(max_length=100, blank=True, null=True)
    attribute2 = models.CharField(max_length=100, blank=True, null=True)
    attribute3 = models.CharField(max_length=100, blank=True, null=True)
    attribute4 = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.item_name


class Listing(models.Model):
    """Model representing a specific listing in an inventory."""
    listing_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name="listings")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="listings")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    promo_start_date = models.DateField(blank=True, null=True)
    promo_end_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    snap_url = models.CharField(max_length=500, unique=True)
    snap_qr_code = models.ImageField(upload_to="qr_codes/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.item.item_name} - {self.price}"

