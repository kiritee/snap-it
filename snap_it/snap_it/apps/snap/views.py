from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Snap
from snap_it.apps.inventory.models import Listing

@login_required
def snap_listing(request, listing_id):
    """
    Handles snapping a listing for the logged-in user.
    """
    listing = get_object_or_404(Listing, listing_id=listing_id)

    snap, created = Snap.objects.get_or_create(
        user=request.user, 
        listing=listing, 
        defaults={"price": listing.price}
    )

    message = "Snap added successfully!" if created else "Snap already exists."
    return JsonResponse({"message": message, "snap_id": snap.snap_id})

