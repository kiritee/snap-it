from rest_framework import serializers
from ..models import Inventory, Item, Listing

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = "__all__"


class ListingSerializer(serializers.ModelSerializer):
    item = ItemSerializer(read_only=True)  # Nested Item details

    class Meta:
        model = Listing
        fields = "__all__"


class InventorySerializer(serializers.ModelSerializer):
    listings = ListingSerializer(many=True, read_only=True)  # Nested Listings

    class Meta:
        model = Inventory
        fields = "__all__"
