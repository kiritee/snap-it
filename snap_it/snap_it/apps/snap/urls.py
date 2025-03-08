from django.urls import path
from .views import snap_listing

app_name = "snaps"

urlpatterns = [
    path("snap/<int:listing_id>/", snap_listing, name="snap-listing"),
]
