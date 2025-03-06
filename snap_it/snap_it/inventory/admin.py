from django.contrib import admin
from .models import Inventory, Item, Listing

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ("inventory_name", "merchant", "created_at", "updated_at")
    search_fields = ("inventory_name", "merchant__email")
    list_filter = ("created_at",)

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("item_name", "category", "created_at", "updated_at")
    search_fields = ("item_name", "category", "ean_number")
    list_filter = ("category",)

@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ("item", "inventory", "price", "is_active", "created_at", "updated_at")
    search_fields = ("item__item_name", "inventory__inventory_name")
    list_filter = ("is_active", "created_at")
