from rest_framework import viewsets, permissions
from rest_framework.response import Response
from ..models import Inventory, Item, Listing
from .serializers import InventorySerializer, ItemSerializer, ListingSerializer

class InventoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing inventories.
    Merchants can create and manage their inventories.
    """
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(merchant=self.request.user)


class ItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing items.
    """
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated]


class ListingViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing listings inside inventories.
    """
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticated]
