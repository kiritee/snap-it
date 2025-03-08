from allauth.account.forms import SignupForm
from allauth.socialaccount.forms import SignupForm as SocialSignupForm
from django import forms
from django.contrib.auth import forms as admin_forms
from django.forms import EmailField
from django.utils.translation import gettext_lazy as _
from .models import User, Customer, Merchant


class UserAdminChangeForm(admin_forms.UserChangeForm):
    """Admin form for changing a User's details."""
    
    class Meta(admin_forms.UserChangeForm.Meta):  # type: ignore[name-defined]
        model = User
        fields = ("email", "role")
        field_classes = {"email": EmailField}
        error_messages = {
            "email": {"unique": _("This email has already been taken.")},
        }





class UserAdminCreationForm(admin_forms.UserCreationForm):
    """
    Form for creating a new User in the Admin Area.
    Allows selecting a role (customer/merchant) at the time of creation.
    """

    ROLE_CHOICES = [
        ("customer", "Customer"),
        ("merchant", "Merchant"),
    ]

    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True)

    class Meta(admin_forms.UserCreationForm.Meta):  # type: ignore[name-defined]
        model = User
        fields = ("email", "role")
        field_classes = {"email": EmailField}
        error_messages = {
            "email": {"unique": _("This email has already been taken.")},
        }

    def save(self, commit=True):
        """
        Override save() to automatically create a Customer or Merchant 
        when a user is created in the Admin panel.
        """
        user = super().save(commit=False)
        
        if commit:
            user.save()
            if user.role == "customer":
                Customer.objects.create(user=user)
            elif user.role == "merchant":
                Merchant.objects.create(user=user)
        
        return user




### **🔹 Customer Admin Forms**
class CustomerAdminChangeForm(forms.ModelForm):
    """Admin form for changing Customer details."""

    class Meta:
        model = Customer
        fields = ["first_name", "last_name", "phone", "address"]

    def clean(self):
        """Ensure the linked user has `role="customer"`."""
        cleaned_data = super().clean()
        if self.instance.user.role != "customer":
            raise forms.ValidationError("The associated user must have role='customer'.")
        return cleaned_data




class CustomerAdminCreationForm(forms.ModelForm):
    """Admin form for creating a Customer."""

    class Meta:
        model = Customer
        fields = ["user", "first_name", "last_name", "phone", "address"]

    def save(self, commit=True):
        """Ensure the linked user has `role="customer"`."""
        customer = super().save(commit=False)
        if customer.user.role != "customer":
            raise forms.ValidationError("The associated user must have role='customer'.")
        if commit:
            customer.save()
        return customer




### **🔹 Merchant Admin Forms**
class MerchantAdminChangeForm(forms.ModelForm):
    """Admin form for changing Merchant details."""

    class Meta:
        model = Merchant
        fields = ["company_name", "phone", "address"]

    def clean(self):
        """Ensure the linked user has `role="merchant"`."""
        cleaned_data = super().clean()
        if self.instance.user.role != "merchant":
            raise forms.ValidationError("The associated user must have role='merchant'.")
        return cleaned_data




class MerchantAdminCreationForm(forms.ModelForm):
    """Admin form for creating a Merchant."""

    class Meta:
        model = Merchant
        fields = ["user", "company_name", "phone", "address"]

    def save(self, commit=True):
        """Ensure the linked user has `role="merchant"`."""
        merchant = super().save(commit=False)
        if merchant.user.role != "merchant":
            raise forms.ValidationError("The associated user must have role='merchant'.")
        if commit:
            merchant.save()
        return merchant




class CustomerForm(forms.ModelForm):
    """Form for Customers to update their profile details."""
    
    class Meta:
        model = Customer
        fields = ["first_name", "last_name", "phone", "address"]




class MerchantForm(forms.ModelForm):
    """Form for Merchants to update their profile details."""

    class Meta:
        model = Merchant
        fields = ["company_name", "phone", "address"]




class UserSignupForm(SignupForm):
    """
    Form that will be rendered on a user sign up section/screen.
    Default fields will be added automatically.
    Check UserSocialSignupForm for accounts created from social.
    """


class UserSocialSignupForm(SocialSignupForm):
    """
    Renders the form when user has signed up using social accounts.
    Default fields will be added automatically.
    See UserSignupForm otherwise.
    """
