from allauth.account.decorators import secure_admin_login
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse

from .forms import UserAdminChangeForm, UserAdminCreationForm, CustomerAdminChangeForm, CustomerAdminCreationForm, MerchantAdminChangeForm, MerchantAdminCreationForm
from .models import User, Customer, Merchant

if settings.DJANGO_ADMIN_FORCE_ALLAUTH:
    # Force the `admin` sign-in process to go through django-allauth
    admin.autodiscover()
    admin.site.login = secure_admin_login(admin.site.login)  # type: ignore[method-assign]


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    """
    Custom admin interface for User model.
    Handles role-based customer/merchant assignment.
    """
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Role & Profile Info"), {"fields": ("role",)}),  # Added role field for assignment
        (_("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    list_display = ["email", "role", "is_superuser"]
    search_fields = ["email"]
    ordering = ["id"]
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "role"),  # Allow selecting role at creation
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        """
        Override save_model to automatically create Customer/Merchant 
        when a User is assigned role='customer' or 'merchant'.
        """
        is_new_user = obj._state.adding

        # If role changed, delete the old profile before saving the new one
        if not is_new_user:
            existing_user = User.objects.get(pk=obj.pk)
            if existing_user.role != obj.role:
                if existing_user.role == "customer":
                    Customer.objects.filter(user=obj).delete()
                elif existing_user.role == "merchant":
                    Merchant.objects.filter(user=obj).delete()

        # Save the user first
        super().save_model(request, obj, form, change)

        # Ensure a Customer or Merchant object is created based on role
        if obj.role == "customer":
            Customer.objects.get_or_create(user=obj)
        elif obj.role == "merchant":
            merchant, created = Merchant.objects.get_or_create(user=obj)
            if created:
                merchant.company_name = f"Merchant {obj.email}"  # Default placeholder
                merchant.save()               

    def response_add(self, request, obj, post_url_continue=None):
        """
        Redirect to the edit page of the newly created Customer/Merchant.
        """
        if obj.role == "customer":
            return HttpResponseRedirect(reverse("admin:users_customer_change", args=[obj.pk]))
        elif obj.role == "merchant":
            return HttpResponseRedirect(reverse("admin:users_merchant_change", args=[obj.pk]))
        return super().response_add(request, obj, post_url_continue)
    
    def response_change(self, request, obj):
        """
        Redirect to the correct edit page if the role was changed.
        """
        if obj.role == "customer":
            return HttpResponseRedirect(reverse("admin:users_customer_change", args=[obj.pk]))
        elif obj.role == "merchant":
            return HttpResponseRedirect(reverse("admin:users_merchant_change", args=[obj.pk]))
        return super().response_change(request, obj)
    

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """
    Custom admin interface for Customer model.
    Ensures only users with role='customer' are assigned as a Customer.
    """
    form = CustomerAdminChangeForm
    add_form = CustomerAdminCreationForm
    list_display = ("user", "first_name", "last_name", "phone", "address")
    search_fields = ("user__email", "first_name", "last_name")
    ordering = ["user__email"]
    fields = ("user", "first_name", "last_name", "phone", "address")

    def save_model(self, request, obj, form, change):
        """
        Ensure only users with `role="customer"` can be assigned as a Customer.
        """
        if obj.user.role != "customer":
            raise ValueError("Only users with role='customer' can be assigned as a Customer.")
        super().save_model(request, obj, form, change)


@admin.register(Merchant)
class MerchantAdmin(admin.ModelAdmin):
    """
    Custom admin interface for Merchant model.
    Ensures only users with role='merchant' can be assigned as a Merchant.
    """
    form = MerchantAdminChangeForm
    add_form = MerchantAdminCreationForm
    list_display = ("user", "company_name", "user", "address")
    search_fields = ("company_name", "user__email")
    ordering = ["company_name"]
    fields = ("user", "company_name", "address")

    def save_model(self, request, obj, form, change):
        """
        Ensure only users with `role="merchant"` can be assigned as a Merchant.
        """
        if obj.user.role != "merchant":
            raise ValueError("Only users with role='merchant' can be assigned as a Merchant.")
        super().save_model(request, obj, form, change)
