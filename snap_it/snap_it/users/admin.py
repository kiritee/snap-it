import csv
import io
import logging
from allauth.account.decorators import secure_admin_login
from django.conf import settings
from django.contrib import admin, messages
from django.shortcuts import redirect
from django.contrib.auth import admin as auth_admin
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse, path
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .forms import UserAdminChangeForm, UserAdminCreationForm, CustomerAdminChangeForm, CustomerAdminCreationForm, MerchantAdminChangeForm, MerchantAdminCreationForm
from .models import User, Customer, Merchant


logger = logging.getLogger(__name__)

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
    actions = ["bulk_upload_customers"]

    def save_model(self, request, obj, form, change):
        """
        Ensure only users with `role="customer"` can be assigned as a Customer.
        """
        if obj.user.role != "customer":
            raise ValueError("Only users with role='customer' can be assigned as a Customer.")
        super().save_model(request, obj, form, change)

    def get_urls(self):
        """Add custom admin URL for bulk uploads."""
        urls = super().get_urls()
        custom_urls = [
            path("bulk-upload/", self.admin_site.admin_view(self.bulk_upload_view), name="bulk-upload-customers"),
        ]
        return custom_urls + urls

    def bulk_upload_view(self, request):
        """Admin panel bulk upload view for customers."""
        if request.method == "POST" and request.FILES.get("csv_file"):
            file = request.FILES["csv_file"]
            csv_data = file.read().decode("utf-8")
            csv_reader = csv.DictReader(io.StringIO(csv_data))

            created, updated, errors = 0, 0, []

            with transaction.atomic():
                for row in csv_reader:
                    email = row.get("email", "").strip()
                    password = row.get("password", "").strip()
                    first_name = row.get("first_name", "").strip()
                    last_name = row.get("last_name", "").strip()
                    phone = row.get("phone", "").strip()
                    address = row.get("address", "").strip()

                    if not email or not password:
                        errors.append(f"Missing email or password: {row}")
                        continue

                    # Validate email format
                    try:
                        validate_email(email)
                    except ValidationError:
                        errors.append(f"Invalid email: {email}")
                        continue

                    # Check if user already exists
                    user, created_user = User.objects.get_or_create(email=email, defaults={"role": "customer"})

                    if created_user:
                        # Bypass password validation and create user
                        user.set_password(password)
                        user.save()
                        created += 1
                    else:
                        updated += 1

                    # **Find and update the existing Customer object**
                    try:
                        customer = Customer.objects.get(user=user)
                        customer.first_name = first_name
                        customer.last_name = last_name
                        customer.phone = phone
                        customer.address = address
                        customer.save()
                    except Customer.DoesNotExist:
                        errors.append(f"Customer object missing for user: {email}")

            messages.success(request, f"Created: {created}, Updated: {updated}, Errors: {len(errors)}")
            if errors:
                logger.warning(f"Errors during bulk upload: {errors}")

            return redirect("..")

        return HttpResponseRedirect(request.META.get("HTTP_REFERER", ".."))
    
    def bulk_upload_customers(self, request, queryset):
        """Admin action to bulk upload customers via CSV."""
        return HttpResponseRedirect(reverse("admin:bulk-upload-customers"))
    bulk_upload_customers.short_description = "Bulk Upload Customers"   

    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions
    

    
#admin.site.register(Customer, CustomerAdmin)




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
    actions = ["bulk_upload_merchants"]

    def save_model(self, request, obj, form, change):
        """
        Ensure only users with `role="merchant"` can be assigned as a Merchant.
        """
        if obj.user.role != "merchant":
            raise ValueError("Only users with role='merchant' can be assigned as a Merchant.")
        super().save_model(request, obj, form, change)


    def get_urls(self):
        """Add custom admin URL for bulk uploads."""
        urls = super().get_urls()
        custom_urls = [
            path("bulk-upload/", self.admin_site.admin_view(self.bulk_upload_view), name="bulk-upload-merchants"),
        ]
        return custom_urls + urls

    def bulk_upload_view(self, request):
        """Admin panel bulk upload view for merchants."""
        if request.method == "POST" and request.FILES.get("csv_file"):
            file = request.FILES["csv_file"]
            csv_data = file.read().decode("utf-8")
            csv_reader = csv.DictReader(io.StringIO(csv_data))

            created, updated, errors = 0, 0, []

            with transaction.atomic():
                for row in csv_reader:
                    email = row.get("email", "").strip()
                    password = row.get("password", "").strip()
                    company_name = row.get("company_name", "").strip()
                    last_name = row.get("last_name", "").strip()
                    phone = row.get("phone", "").strip()
                    address = row.get("address", "").strip()

                    if not email or not password:
                        errors.append(f"Missing email or password: {row}")
                        continue

                    # Validate email format
                    try:
                        validate_email(email)
                    except ValidationError:
                        errors.append(f"Invalid email: {email}")
                        continue

                    # Check if user already exists
                    user, created_user = User.objects.get_or_create(email=email, defaults={"role": "merchant"})

                    if created_user:
                        # Bypass password validation and create user
                        user.set_password(password)
                        user.save()
                        created += 1
                    else:
                        updated += 1

                    # **Find and update the existing Customer object**
                    try:
                        merchant = Merchant.objects.get(user=user)
                        merchant.company_name = company_name
                        merchant.last_name = last_name
                        merchant.phone = phone
                        merchant.address = address
                        merchant.save()
                    except Merchant.DoesNotExist:
                        errors.append(f"Merchant object missing for user: {email}")

            messages.success(request, f"Created: {created}, Updated: {updated}, Errors: {len(errors)}")
            if errors:
                logger.warning(f"Errors during bulk upload: {errors}")

            return redirect("..")

        return HttpResponseRedirect(request.META.get("HTTP_REFERER", ".."))
    
    def bulk_upload_merchants(self, request, queryset):
        """Admin action to bulk upload merchants via CSV."""
        return HttpResponseRedirect(reverse("admin:bulk-upload-merchants"))
    bulk_upload_merchants.short_description = "Bulk Upload Merchants"   

    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions
    
