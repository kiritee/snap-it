
from typing import ClassVar
from django.core.cache import cache

from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.utils.timezone import now
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken


from .managers import UserManager


class User(AbstractUser):
    """
    Default custom user model for Snap-It!.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    ROLE_CHOICES = [
        ("customer", "Customer"),
        ("merchant", "Merchant"),
        ("admin", "Admin"),
    ]

    email = models.EmailField(_("email address"), unique=True)
    username = None  # type: ignore[assignment]
    role = models.CharField(_("customer / merchant"), max_length=10, choices=ROLE_CHOICES, default="customer")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects: ClassVar[UserManager] = UserManager()


    def save(self, *args, **kwargs):
            """
            Override save() to:
            - Create Customer/Merchant on first save.
            - If role changes, delete the previous Customer/Merchant and create a new one.
            """
            
            if self.role in ["customer", "merchant"]:
                self.is_staff = False
                self.is_superuser = False
            
            # logout all sessions if password is changed
            if self.pk:  # Ensure this is an existing user
                old_password = User.objects.get(pk=self.pk).password
                if old_password != self.password:  # Password changed
                    self.logout_all_sessions()  # Blacklist all JWT tokens

            # check for role change while updating user
            is_new = self._state.adding  # Check if user is newly created
            previous_role = None  # Store previous role for role change check
            if not is_new:  # User already exists, check role change
                user_in_db = User.objects.get(pk=self.pk)
                previous_role = user_in_db.role

            super().save(*args, **kwargs)  # Save user first

            # If new user, create the appropriate object
            if is_new:
                if self.role == "customer":
                    Customer.objects.create(user=self)
                elif self.role == "merchant":
                    Merchant.objects.create(user=self)
            else:
                # If role changed, remove old object and create a new one
                if previous_role != self.role:
                    if previous_role == "customer":
                        Customer.objects.filter(user=self).delete()
                    elif previous_role == "merchant":
                        Merchant.objects.filter(user=self).delete()

                    # Create new object based on updated role
                    if self.role == "customer":
                        Customer.objects.create(user=self)
                    elif self.role == "merchant":
                        Merchant.objects.create(user=self)
        


    def __str__(self):
        return f"{self.email} ({self.role})"


    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.
        Returns:
            str: URL for user detail.
        """
        return reverse("users:detail", kwargs={"pk": self.id})


    def logout_all_sessions(self):
        """Blacklist all refresh tokens when the password changes."""
        tokens = OutstandingToken.objects.filter(user=self)
        for token in tokens:
            token.blacklist()
        
        # Expire all active access tokens by storing a logout timestamp
        cache.set(f"user_logout_{self.id}", "logout", timeout=None)  # No expiry



class Customer(models.Model):
    """
    Customer model extending User.
    Stores additional fields specific to customers.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    first_name = models.CharField(_("First Name"), max_length=150, blank=True)
    last_name = models.CharField(_("Last Name"), max_length=150, blank=True)
    phone = models.CharField(_("Phone Number"),max_length=15, blank=True, null=True)
    address = models.TextField(_("Address"), blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} (Customer: {self.user.email})"


    def get_absolute_url(self) -> str:
        """Get URL for customer's detail view.
        Returns:
            str: URL for customers detail.
        """
        return reverse("customers:detail", kwargs={"pk": self.user.id})


    def delete(self, *args, **kwargs):
        """Ensure deleting a Customer also deletes the associated User."""
        user = self.user  # Store user reference before deleting Customer
        super().delete(*args, **kwargs)  # Delete Customer first
        user.delete()  # Then delete the associated User




class Merchant(models.Model):
    """
    Merchant model extending User.
    Stores additional fields specific to merchants.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    company_name = models.CharField(_("Company Name"), max_length=255, unique=True)
    phone = models.CharField(_("Phone Number"), max_length=15, blank=True, null=True)
    address = models.TextField(_("Registered Address"), blank=True, null=True)

    def __str__(self):
        return f"{self.company_name} (Merchant: {self.user.email})"


    def get_absolute_url(self) -> str:
        """Get URL for merchant's detail view.
        Returns:
            str: URL for merchant detail.
        """
        return reverse("merchants:detail", kwargs={"pk": self.user.id})

    
    def delete(self, *args, **kwargs):
        """Ensure deleting a Merchant also deletes the associated User."""
        user = self.user  # Store user reference before deleting Merchant
        super().delete(*args, **kwargs)  # Delete Merchant first
        user.delete()  # Then delete the associated User