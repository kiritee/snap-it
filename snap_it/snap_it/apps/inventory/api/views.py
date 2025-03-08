import csv
import io
import logging
from rest_framework import viewsets, permissions, filters, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from ..models import Inventory, Item, Listing
from .serializers import InventorySerializer, ItemSerializer, ListingSerializer

logger = logging.getLogger(__name__)

class InventoryViewSet(viewsets.ModelViewSet):
    """
    API for managing Inventories
    - Read: Everyone
    - Create/Update/Delete: Only Merchant who owns it
    - Supports CSV Upload for Bulk Listing Creation
    """
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get_permissions(self):
        """Only allow merchants to modify inventories."""
        if self.action in ["create", "update", "destroy"]:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        """Ensure only the merchant can create inventory."""
        serializer.save(merchant=self.request.user)

    def perform_destroy(self, instance):
        """Soft delete inventory."""
        instance.is_active = False
        instance.save()
        return Response({"message": "Inventory soft-deleted"}, status=204)


    @action(detail=False, methods=["POST"], url_path="upload-csv")
    def upload_csv(self, request):
        """
        Merchant uploads CSV → Creates Inventory → Adds Listings.
        - CSV filename = Inventory name
        - Each row = Listing (if `item_id` exists)
        """
        merchant = request.user
        if merchant.role != "Merchant":
            return Response({"error": "Only merchants can upload inventories."}, status=403)

        file = request.FILES.get("file")
        if not file:
            return Response({"error": "CSV file is required"}, status=400)

        # Create Inventory with filename as inventory name
        inventory_name = file.name.split(".")[0]  # Remove file extension
        inventory = Inventory.objects.create(merchant=merchant, inventory_name=inventory_name)

        # Read CSV File
        csv_data = file.read().decode("utf-8")
        csv_reader = csv.DictReader(io.StringIO(csv_data))

        not_found_items = []  # Log items not found
        created_listings = []

        for row in csv_reader:
            item_id = row.get("item_id")
            price = row.get("price")

            # Validate Data
            if not item_id or not price:
                continue

            try:
                item = Item.objects.get(id=item_id)
                listing = Listing.objects.create(
                    inventory=inventory,
                    item=item,
                    price=price,
                )
                created_listings.append(ListingSerializer(listing).data)

            except Item.DoesNotExist:
                not_found_items.append(item_id)

        logger.warning(f"Invalid Item IDs: {not_found_items}")

        return Response(
            {
                "message": f"Inventory '{inventory_name}' created successfully.",
                "total_listings": len(created_listings),
                "not_found_items": not_found_items,
            },
            status=201,
        )








class ItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing items.
    """
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        """Allow anyone to read, but only admin can modify."""
        if self.action in ["create", "update", "destroy"]:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    def perform_destroy(self, instance):
        """Soft delete the item and cascade to Listings."""
        instance.deleted = True  # Soft delete Item
        instance.save()
        Listing.objects.filter(item=instance).update(is_active=False)  # Soft delete Listings
        return Response({"message": "Item soft-deleted & Listings disabled"}, status=204)




class ListingViewSet(viewsets.ModelViewSet):
    """
    API for managing Listings
    - Read: Everyone
    - Create/Update/Delete: Only Merchant who owns the Inventory
    - Search by Item
    """
    queryset = Listing.objects.filter(is_active=True)
    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [filters.SearchFilter]
    search_fields = ["item__item_name", "item__ean_number", "inventory__inventory_name"]

    def get_permissions(self):
        """Only allow merchants to modify Listings."""
        if self.action in ["create", "update", "destroy"]:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        """Ensure the merchant owns the inventory."""
        inventory = serializer.validated_data["inventory"]
        if inventory.merchant != self.request.user:
            return Response({"error": "Not authorized"}, status=403)
        serializer.save()

    def perform_destroy(self, instance):
        """Soft-delete listings."""
        instance.is_active = False
        instance.save()
        return Response({"message": "Listing soft-deleted"}, status=204)