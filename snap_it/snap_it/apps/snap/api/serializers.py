from rest_framework import serializers
from snap_it.apps.snap.models import Snap
from snap_it.apps.inventory.models import Listing

class SnapSerializer(serializers.ModelSerializer):
    """Serializer for Snap objects"""
    
    listing_name = serializers.CharField(source="listing.item.item_name", read_only=True)  
    listing_price = serializers.DecimalField(source="listing.price", max_digits=10, decimal_places=2, read_only=True)
    snap_id = serializers.IntegerField(read_only=True)  # ✅ Define snap_id explicitly


    class Meta:
        model = Snap
        fields = ["snap_id", "user", "listing", "listing_name", "listing_price", "price", "created_at"]
        read_only_fields = ["snap_id", "user", "listing_name", "listing_price", "created_at"]

    def create(self, validated_data):
        """Ensure user is set automatically"""
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            validated_data["user"] = request.user
        return super().create(validated_data)
