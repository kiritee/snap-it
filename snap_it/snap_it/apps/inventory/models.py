from django.db import models, transaction
from django.conf import settings
import uuid
from snap_it.users.models import User
from django.urls import reverse

import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from django.db.models import Q, F, Exists, OuterRef




class Inventory(models.Model):
    """Model representing a batch of items uploaded by a merchant."""
    inventory_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchant = models.ForeignKey(User, on_delete=models.CASCADE, related_name="inventories")
    inventory_name = models.CharField(max_length=255, blank=True, null=True)
    listings= models.ManyToManyField("Listing", related_name="inventories", blank=True)
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
    model_desc = models.CharField(max_length=100, blank=True, null=True)
    model_year = models.CharField(max_length=4, blank=True, null=True)
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
    listing_id = models.AutoField(primary_key=True)
    inventory = models.ForeignKey("Inventory", on_delete=models.CASCADE)
    item = models.ForeignKey("Item", on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    promo_start_date = models.DateField(null=True, blank=True)
    promo_end_date = models.DateField(null=True, blank=True)
    is_live = models.BooleanField(default=True)  # New field
    is_active = models.BooleanField(default=True)
    snap_url = models.URLField(max_length=500, unique=True, blank=True, null=True)  # Store the snap URL
    snap_qr_code = models.ImageField(upload_to="qr_codes/", blank=True, null=True)  # QR Code Image
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['inventory', 'item'],
                condition=Q(is_live=True),
                name="unique_live_listing_per_item_per_merchant"
            )
        ]


    def generate_snap_url(self):
        """Generate a unique URL for this listing's snap feature"""
        return reverse("snaps:snap-listing", kwargs={"listing_id": self.listing_id})
    
    def generate_qr_code(self):
        """Generate a QR code linking to the snap_url"""
        qr = qrcode.make(self.snap_url)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        self.snap_qr_code.save(f"qr_{self.listing_id}.png", ContentFile(buffer.getvalue()), save=False)
        buffer.close()

    def save(self, *args, **kwargs):
        """
        Override save() to enforce only one live listing per item per merchant.
        If a new listing is created with is_live=True, deactivate the old one.
        """
        if self.is_live:
            # Find old live listing for the same merchant and item
            old_listing = Listing.objects.filter(
                inventory__merchant=self.inventory.merchant,
                item=self.item,
                is_live=True
            ).exclude(pk=self.pk).first()

            if old_listing:
                old_listing.is_live = False
                old_listing.save(update_fields=["is_live"])

        super().save(*args, **kwargs)  # Ensure the object is saved first
        update_live_inventory(self)
        
        """Override save method to auto-generate snap_url if not set"""
        update_fields = []

        if not self.snap_url:
            self.snap_url = self.generate_snap_url()
            update_fields.append("snap_url")

        if not self.snap_qr_code:
            self.generate_qr_code()
            update_fields.append("snap_qr_code")

        # Save only the modified fields to prevent triggering auto-increment
        if update_fields:
            super().save(update_fields=update_fields)

    def __str__(self):
        return f"Listing {self.listing_id} - {self.item}"
    



class LiveInventory(models.Model):
    """Stores live listings per merchant for fast retrieval."""
    merchant = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE, related_name="live_inventory")
    listings = models.ManyToManyField("Listing", related_name="live_inventory")

    def __str__(self):
        return f"Live Inventory for {self.merchant.user.email}"
    

    def update_live_inventory(self):
        """Syncs the live inventory with latest live listings."""
        self.listings.set(Listing.objects.filter(
            inventory__merchant=self.merchant, is_live=True
        ))
