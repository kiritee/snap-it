import csv
import io
import logging
from django import forms
from django.db import transaction
from django.contrib import admin, messages
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.shortcuts import redirect, render
from django.urls import path
from django.http import HttpResponseRedirect
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Inventory, Item, Listing, LiveInventory
from django.template.response import TemplateResponse
from datetime import datetime
from snap_it.users.models import Merchant
from django.db.models import Q

logger = logging.getLogger(__name__)


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



class ListingInline(admin.TabularInline):
    model = Listing  # ✅ Use Listing instead of through table
    extra = 1
    verbose_name = "Listing"
    verbose_name_plural = "Listings"
    readonly_fields = ("listing",)  # ✅ Keep `listing_link` & `item_name` read-only
    fields = ("listing","price")  # ✅ `price` is now editable

    def listing(self, obj):
        """Create a clickable link to the Listing admin page."""
        if obj.pk:  # Only show if the Listing exists
            return format_html('<a href="/admin/inventory/listing/{}/change/">{}</a>', obj.pk, obj)
        return "-"



@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
#    form = InventoryAdminForm
    fields = ("inventory_name", "merchant")
    list_display = ("inventory_name", "merchant", "created_at", "updated_at")
    search_fields = ("inventory_name", "merchant__email")
    list_filter = ("created_at",)
    inlines = [ListingInline]

    ### ✅ Correctly Inject Bulk Upload Button Next to "Add Item +" ###
    change_list_template = "admin/inventory/item_change_list.html"


    ### ✅ Adding Custom Admin URLs for Bulk Upload/Delete ###
    def get_urls(self):
        """Add custom admin URL for bulk uploads."""
        urls = super().get_urls()
        custom_urls = [
            path("bulk-upload/", self.admin_site.admin_view(self.bulk_upload_view), name="bulk-upload-listings"),
            path("bulk-delete/", self.admin_site.admin_view(self.bulk_delete_view), name="bulk-delete-listings"),
        ]
        return custom_urls + urls

    
    ### ✅ Bulk Upload View (File Upload Form) ###
    def bulk_upload_view(self, request):
        """Admin bulk upload view for inventory listings."""
        if request.method == "POST" and request.FILES.get("csv_file"):
            csv_file = request.FILES.get("csv_file")
            if not csv_file or not csv_file.name.endswith(".csv"):
                messages.error(request, "Invalid file format. Please upload a CSV file.")
                return redirect(request.path)


            file_name = csv_file.name.rsplit(".", 1)[0]  # Extract full file name and Remove file extension
            # Split using ' - ' to extract company_name and inventory_name
            parts = file_name.split(" - ", 1)  # Split at the first occurrence

            if len(parts) == 2 and parts[1].strip():  
                company_name, inventory_name = parts
            else:
                company_name = parts[0]  # Take the first part as the company name
                inventory_name = ""  # Set inventory_name as blank if missing


            if not Merchant.objects.filter(company_name=company_name).exists():
                messages.error(request, "Invalid company name. Please upload a CSV file with merchant name in filename.")
                return redirect(request.path)

            merchant = Merchant.objects.get(company_name=company_name).user
            if not inventory_name:
                inventory_name = f"{company_name} - {datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"

            if not Inventory.objects.filter(merchant=merchant, inventory_name = inventory_name).exists():
                inventory = Inventory.objects.create(
                    merchant = merchant,
                    inventory_name = inventory_name,
                )
            else: 
                inventory = Inventory.objects.get(merchant=merchant, inventory_name = inventory_name)




            error_rows = []
            created_count = 0
            updated_count = 0

            inventory.listings.set([]) 

            decoded_file = csv_file.read().decode("utf-8").splitlines()
            reader = csv.DictReader(decoded_file)

            with transaction.atomic():
                for row in reader:
                    try:
                        print(f"Processing row: {row}")  # Debug: Print row being processed
                        logger.info(f"Processing row: {row}")  # Log to Django server logs

                        # Fetch the item from DB
                        item_name = row.get("item_name", "").strip()
                        item = Item.objects.filter(item_name=item_name).first()

                        if not item:
                            print(f"Item '{item_name}' not found in DB. Skipping row.")
                            logger.warning(f"Item '{item_name}' not found in DB. Skipping row.")
                            error_rows.append(row)
                            continue  # Skip this row if item doesn't exist

                        print(f"Found item: {item}")  # Debugging  

                        promo_start_date = row.get("promo_start_date", "") or "2999-12-31"
                        promo_end_date = row.get("promo_end_date", "") or "2999-12-31"
                        # Create listing
                        listing, created = Listing.objects.update_or_create(
                            inventory=inventory,
                            item=item,
                            defaults={  
                                "price": row.get("price"),
                                "promo_start_date": datetime.strptime(promo_start_date, "%Y-%m-%d").date(),
                                "promo_end_date": datetime.strptime(promo_end_date, "%Y-%m-%d").date(),
                            }
                        )
                        print("Listing Created")
                        listing.save()

                        if created:
                            print(f"New listing created: {listing}")
                            logger.info(f"New listing created: {listing}")
                            created_count += 1
                        else:
                            print(f"Listing already exists, updating: {listing}")
                            logger.info(f"Listing already exists, updating: {listing}")
                            updated_count += 1

                        # Ensure listing is linked to inventory
                        inventory.listings.add(listing)
                        print(f"Added listing to inventory: {inventory.inventory_name}")
                        logger.info(f"Added listing to inventory: {inventory.inventory_name}")

                    except Exception as e:
                        print(f"Error processing row {row}: {e}")
                        logger.error(f"Error processing row {row}: {e}", exc_info=True)
                        error_rows.append(row)

            if error_rows:
                messages.warning(request, f"Some rows failed: {len(error_rows)}")
            messages.success(request, f"Upload successful: {created_count} created, {updated_count} updated.")

            return redirect("../")
        
        return TemplateResponse(request, "admin/bulk_upload_form.html")


    def bulk_delete_view(self, request):
        """Admin bulk delete view for inventory listings."""
        if request.method == "POST" and request.FILES.get("csv_file"):
            file = request.FILES["csv_file"]
            csv_data = file.read().decode("utf-8")
            csv_reader = csv.DictReader(io.StringIO(csv_data))

            inventory_id = request.POST.get("inventory_id")
            inventory = Inventory.objects.get(pk=inventory_id)

            deleted, not_found = 0, []

            with transaction.atomic():
                for row in csv_reader:
                    item_id = row.get("item_id")
                    if not item_id:
                        continue
    
                    try:
                        item = Item.objects.get(item_id=item_id)
                        listing = Listing.objects.get(inventory=inventory, item=item)
                        listing.delete()
                        deleted += 1

                    except Item.DoesNotExist:
                        not_found.append(item_id)
                    except Listing.DoesNotExist:
                        pass    # Listing already deleted
                
            messages.success(request, f"Deleted: {deleted}, Not Found: {len(not_found)}")
            return redirect("..")

        return HttpResponseRedirect(request.META.get("HTTP_REFERER", ".."))





@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("item_id", "item_name", "brand", "model_desc", "model_year", "colour", "category", "sub_category", "created_at", "updated_at",)
    search_fields = ("item_name", "category", "ean_number")
    list_filter = ("category","brand",)

    ### ✅ Correctly Inject Bulk Upload Button Next to "Add Item +" ###
    change_list_template = "admin/inventory/item_change_list.html"


    ### ✅ Adding Custom Admin URLs for Bulk Upload/Delete ###
    def get_urls(self):
        """Add custom admin URL for bulk uploads."""
        urls = super().get_urls()
        custom_urls = [
            path("bulk-upload/", self.admin_site.admin_view(self.bulk_upload_view), name="bulk-upload-items"),
            path("bulk-delete/", self.admin_site.admin_view(self.bulk_delete_view), name="bulk-delete-items"),
        ]
        return custom_urls + urls


    ### ✅ Bulk Upload View (File Upload Form) ###
    def bulk_upload_view(self, request):
        """Handles bulk upload via CSV in Django Admin."""
        if request.method == "POST":
            csv_file = request.FILES.get("csv_file")
            if not csv_file or not csv_file.name.endswith(".csv"):
                messages.error(request, "Invalid file format. Please upload a CSV file.")
                return redirect(request.path)

            decoded_file = csv_file.read().decode("utf-8").splitlines()
            reader = csv.DictReader(decoded_file)

            error_rows = []
            created_count = 0
            updated_count = 0

            with transaction.atomic():
                for row in reader:
                    try:
                        # Ensure required fields exist
                        item_name = row.get("item_name", "").strip()

                        if not item_name:
                            error_rows.append(row)
                            continue

                        item, created = Item.objects.update_or_create(
                            item_name=item_name,  # Lookup by item_name instead of item_id
                            defaults={
                                "item_description": row.get("item_description", ""),
                                "brand": row.get("brand", ""),
                                "model_desc": row.get("model_desc", ""),
                                "model_year": row.get("model_year", ""),
                                "model_number": row.get("model_number", ""),
                                "category": row.get("category", ""),
                                "sub_category": row.get("sub_category", ""),
                                "ean_number": row.get("ean_number", ""),
                                "colour": row.get("colour", ""),
                                "attribute1": row.get("attribute1", ""),
                                "attribute2": row.get("attribute2", ""),
                                "attribute3": row.get("attribute3", ""),
                                "attribute4": row.get("attribute4", ""),
                            },
                        )
                        if created:
                            created_count += 1
                        else:
                            updated_count += 1
                    except Exception as e:
                        error_rows.append(row)

            if error_rows:
                messages.warning(request, f"Some rows failed: {len(error_rows)}")
            messages.success(request, f"Upload successful: {created_count} created, {updated_count} updated.")

            return redirect("../")

        return TemplateResponse(request, "admin/bulk_upload_form.html")



    ### ✅ Bulk Delete View (CSV-Based Deletion) ###
    def bulk_delete_view(self, request):
        """Bulk delete items via CSV."""
        if request.method == "POST" and request.FILES.get("csv_file"):
            file = request.FILES["csv_file"]
            csv_data = file.read().decode("utf-8")
            csv_reader = csv.DictReader(io.StringIO(csv_data))

            deleted, not_found = 0, []

            with transaction.atomic():
                for row in csv_reader:
                    item_id = row.get("item_id")
                    if not item_id:
                        continue

                    try:
                        item = Item.objects.get(item_id=item_id)
                        item.delete()
                        deleted += 1
                    except Item.DoesNotExist:
                        not_found.append(item_id)

            messages.success(request, f"Deleted: {deleted}, Not Found: {len(not_found)}")
            return redirect("..")

        return HttpResponseRedirect(request.META.get("HTTP_REFERER", ".."))




@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ("item", "inventory", "price", "is_live", "is_active", "created_at", "updated_at")
    search_fields = ("item__item_name", "inventory__inventory_name")
    list_filter = ("inventory__merchant", "is_active", "created_at")


    # def get_actions(self, request):
    #     """Disable delete action for Listings."""
    #     actions = super().get_actions(request)
    #     actions.pop("delete_selected", None)
    #     return actions 
    
    # def has_delete_permission(self, request, obj=None):
    #     return False    # Disable delete permission
    
    # def get_readonly_fields(self, request, obj=None):
    #     return [field.name for field in self.model._meta.fields]    # Disable editing


    def get_urls(self):
        """Add custom admin URL for bulk uploads."""
        urls = super().get_urls()
        custom_urls = [
            path("bulk-upload/", self.admin_site.admin_view(self.bulk_upload_view), name="bulk-upload-listings"),
        ]
        return custom_urls + urls
    
    def bulk_upload_view(self, request):
        """Admin bulk upload view for listings."""
        if request.method == "POST" and request.FILES.get("csv_file"):
            file = request.FILES["csv_file"]
            csv_data = file.read().decode("utf-8")
            csv_reader = csv.DictReader(io.StringIO(csv_data))

            created, updated, errors = 0, 0, []

            with transaction.atomic():
                for row in csv_reader:
                    item_id = row.get("item_id")
                    inventory_id = row.get("inventory_id")
                    price = row.get("price")
                    quantity = row.get("quantity", 1)

                    if not item_id or not inventory_id or not price:
                        errors.append(row)
                        continue

                    item = Item.objects.get(item_id=item_id)
                    inventory = Inventory.objects.get(pk=inventory_id)
                    listing, created_flag = Listing.objects.update_or_create(
                        inventory=inventory,
                        item=item,
                        defaults={
                            "price": price,
                            "quantity": quantity,
                        },
                    )

                    if created_flag:
                        created += 1
                    else:
                        updated += 1

            messages.success(request, f"Created: {created}, Updated: {updated}, Errors: {len(errors)}")
            return redirect("..")
        
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", ".."))
    

    def get_queryset(self, request):
        queryset = super().get_queryset(request).select_related("item", "inventory")
        return queryset  # Default to live listings only

    def merchant_name(self, obj):
        """Show Merchant name in Admin."""
        return obj.inventory.merchant.user.email if obj.inventory.merchant else "N/A"

    merchant_name.short_description = "Merchant"

    
    def item(self, obj):
        return obj.item.item_name

    def inventory(self, obj):
        return obj.inventory.inventory_name
    
    item.short_description = "Item"
    inventory.short_description = "Inventory"
    


@admin.register(LiveInventory)
class LiveInventoryAdmin(admin.ModelAdmin):
    list_display = ("merchant", "get_live_listings")
    search_fields = ("merchant__user__email",)

    def get_live_listings(self, obj):
        return ", ".join([listing.item.item_name for listing in obj.listings.all()])

    get_live_listings.short_description = "Live Listings"








