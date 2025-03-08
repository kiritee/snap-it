from django.conf import settings
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.routers import SimpleRouter

from snap_it.users.api.views import UserViewSet, CustomerViewSet, MerchantViewSet, UserRegistrationView, PasswordChangeView
from snap_it.apps.inventory.api.views import InventoryViewSet, ItemViewSet, ListingViewSet
from snap_it.apps.snap.api.views import SnapViewSet  # <-- Import Snap API ViewSet

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from snap_it.users.api.token_serializers import CustomTokenObtainPairSerializer

router = DefaultRouter() if settings.DEBUG else SimpleRouter()

router.register("users", UserViewSet)
router.register("customers", CustomerViewSet)
router.register("merchants", MerchantViewSet)
router.register('inventories', InventoryViewSet)
router.register('items', ItemViewSet)
router.register('listings', ListingViewSet)
router.register("snaps", SnapViewSet, basename="snap")  # <-- Register Snap API

app_name = "api"

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer  # 👈 Use the modified serializer


urlpatterns = [
    path("", include(router.urls)),
    path("register/", UserRegistrationView.as_view(), name="user-register"),  # Dedicated endpoint for registration
    path("password/change/", PasswordChangeView.as_view(), name="password_change"),

    path("token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"), 
]


