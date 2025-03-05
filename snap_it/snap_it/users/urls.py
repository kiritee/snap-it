from django.urls import path, include
from .views import (
    dashboard_redirect,
    user_detail_view,
    user_update_view,
    user_redirect_view,
    customer_detail_view,
    merchant_detail_view,
    customer_update_view,
    merchant_update_view,
)

app_name = "users"

urlpatterns = [

    path("accounts/", include("allauth.urls")),

    # Web-based User Routes
    path("users/<int:pk>/", user_detail_view, name="detail"),
    path("users/update/", user_update_view, name="update"),
    path("users/redirect/", user_redirect_view, name="redirect"),

    # Dashboard Redirect
    path("dashboard/", dashboard_redirect, name="dashboard_redirect"),

    # Web-based Customer Profile Routes
    path("customers/<int:pk>/", customer_detail_view, name="customer_detail"),
    path("customers/update/", customer_update_view, name="customer_update"),

    # Web-based Merchant Profile Routes
    path("merchants/<int:pk>/", merchant_detail_view, name="merchant_detail"),
    path("merchants/update/", merchant_update_view, name="merchant_update"),

    # Include API Routes Separately
    path("api/", include("users.api.urls")),  
]
