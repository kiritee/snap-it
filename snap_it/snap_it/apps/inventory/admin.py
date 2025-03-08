from django.contrib import admin
from .models import Inventory, Item, Listing
from django import forms

class InventoryAdminForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:  # If inventory exists
            self.fields["listings"].queryset = Listing.objects.filter(inventory=self.instance)
        else:
            self.fields["listings"].queryset = Listing.objects.none()  # Empty for new inventory

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    form = InventoryAdminForm
    list_display = ("inventory_name", "merchant", "created_at", "updated_at")
    search_fields = ("inventory_name", "merchant__email")
    list_filter = ("created_at",)

#admin.site.register(Inventory, InventoryAdmin)





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





