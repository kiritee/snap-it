from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    UserViewSet,
    CustomerViewSet,
    MerchantViewSet,
    UserDetailAPI, 
    CustomerDetailAPI, 
    MerchantDetailAPI, 
    CustomerUpdateAPI, 
    MerchantUpdateAPI,
    PasswordChangeView
)

# DRF Router for ViewSets
router = DefaultRouter()
router.register(r"user", UserViewSet, basename="user")
router.register(r"customer", CustomerViewSet, basename="customer")
router.register(r"merchant", MerchantViewSet, basename="merchant")

urlpatterns = [
    path("", include(router.urls)),  # Includes all ViewSet routes

    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # API Endpoints
    path("user/", UserDetailAPI.as_view(), name="user_api"),
    path("customer/", CustomerDetailAPI.as_view(), name="customer_api"),
    path("merchant/", MerchantDetailAPI.as_view(), name="merchant_api"),
    path("customer/update/", CustomerUpdateAPI.as_view(), name="customer_update_api"),
    path("merchant/update/", MerchantUpdateAPI.as_view(), name="merchant_update_api"),

    path("password/change/", PasswordChangeView.as_view(), name="password_change"),


]