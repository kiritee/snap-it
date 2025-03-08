from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Listing, Snap

'''
@login_required
def snap_listing(request, listing_id):
    """
    When a user clicks the snap_url, add the listing to their Snaps.
    If the user is not logged in, redirect to login.
    """
    listing = get_object_or_404(Listing, listing_id=listing_id)
    
    # Create a Snap record
    snap, created = Snap.objects.get_or_create(
        user=request.user, 
        listing=listing, 
        defaults={"price": listing.price}
    )

    if created:
        message = "Snap added successfully!"
    else:
        message = "Snap already exists."

    return JsonResponse({"message": message, "snap_id": snap.id})

'''