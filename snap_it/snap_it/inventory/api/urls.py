from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InventoryViewSet, ItemViewSet, ListingViewSet

router = DefaultRouter()
router.register(r'inventories', InventoryViewSet)
router.register(r'items', ItemViewSet)
router.register(r'listings', ListingViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
