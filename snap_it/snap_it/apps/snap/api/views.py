from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404

from snap_it.apps.snap.models import Snap
from snap_it.apps.inventory.models import Listing
from .serializers import SnapSerializer
from snap_it.apps.inventory.api.serializers import ListingSerializer, ItemSerializer

class SnapViewSet(viewsets.ModelViewSet):
    """
    API endpoint for users to create, retrieve, and manage snaps.
    """
    serializer_class = SnapSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Snap.objects.all()

    def get_queryset(self):
        """
        Users can only view their own snaps.
        """
        return Snap.objects.filter(user=self.request.user).select_related("listing__item")


    def perform_create(self, serializer):
        """Ensure only customers can create snaps."""
        if self.request.user.role != "customer":
            return Response({"error": "Only customers can snap items"}, status=403)
        serializer.save(user=self.request.user)


    @action(detail=True, methods=["DELETE"], url_path="remove")
    def remove_snap(self, request, pk=None):
        """
        Custom action to remove a snap.
        """
        snap = get_object_or_404(Snap, pk=pk, user=request.user)
        snap.delete()
        return Response({"message": "Snap removed successfully"}, status=204)
    
    
    @action(detail=False, methods=["POST"], url_path="snap-listing/(?P<listing_id>\\d+)")
    def snap_listing(self, request, listing_id=None):
        """
        Custom action to create a snap from a listing.
        """
        listing = get_object_or_404(Listing, pk=listing_id)
        snap = Snap.objects.create(user=request.user, listing=listing, price=listing.price)
        serializer = self.get_serializer(snap)
        return Response(serializer.data, status=201)


    @action(detail=True, methods=["GET"], url_path="listing-info")
    def get_snap_details(self, request, pk=None):
        """
        Get Item and all Listings associated with a Snap.
        """
        snap = get_object_or_404(Snap, pk=pk, user=request.user)
        listing = snap.listing
        item = listing.item
        all_listings = Listing.objects.filter(item=item, is_active=True, is_live=True)

        return Response({
            "item": ItemSerializer(item).data,
            "snap_listing": ListingSerializer(listing).data,
            "other_listings": ListingSerializer(all_listings, many=True).data
        })

