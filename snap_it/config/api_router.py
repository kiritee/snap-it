from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter
from snap_it.users.api.views import UserViewSet, CustomerViewSet, MerchantViewSet
from snap_it.inventory.api.views import InventoryViewSet, ItemViewSet, ListingViewSet

router = DefaultRouter() if settings.DEBUG else SimpleRouter()

# User-related APIs
router.register("users", UserViewSet)
router.register("customers", CustomerViewSet)
router.register("merchants", MerchantViewSet)

# Inventory-related APIs
router.register("inventories", InventoryViewSet)
router.register("items", ItemViewSet)
router.register("listings", ListingViewSet)

app_name = "api"
urlpatterns = router.urls
