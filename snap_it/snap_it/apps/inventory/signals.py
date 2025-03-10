from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Listing, LiveInventory

@receiver(post_save, sender=Listing)
def enforce_single_live_listing(sender, instance, **kwargs):
    """
    Ensures only one live listing exists per (merchant, item).
    If a new live listing is added, old live listing is disabled.
    """
    if instance.is_live:
        Listing.objects.filter(
            inventory__merchant=instance.inventory.merchant,
            item=instance.item,
            is_live=True
        ).exclude(pk=instance.pk).update(is_live=False)




@receiver(post_save, sender=Listing)
def update_live_inventory(sender, instance, **kwargs):
    """Automatically updates LiveInventory when a listing is created or updated."""
    merchant = instance.inventory.merchant

    if instance.is_live:
        # Ensure merchant has a LiveInventory instance
        live_inventory, created = LiveInventory.objects.get_or_create(merchant=merchant)

        # Remove previous listing of the same item (if exists)
        live_inventory.listings.filter(item=instance.item).update(is_live=False)

        # Add new listing to live inventory
        live_inventory.listings.add(instance)

    else:
        # If a listing becomes inactive, remove it from LiveInventory
        LiveInventory.objects.filter(merchant=merchant, listings=instance).update(
            listings=models.F("listings").remove(instance)
        )
