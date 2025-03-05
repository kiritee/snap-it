from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import QuerySet
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView
from django.views.generic import RedirectView
from django.views.generic import UpdateView
from django.shortcuts import get_object_or_404, redirect


from rest_framework.generics import RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated

from .models import User, Customer, Merchant
from .forms import CustomerForm, MerchantForm

class CustomerOnlyMixin(UserPassesTestMixin):
    """Restrict access to customers only."""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == "customer"


class MerchantOnlyMixin(UserPassesTestMixin):
    """Restrict access to merchants only."""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == "merchant"



### ** Dashboard Redirect View**
@login_required
def dashboard_redirect(request):
    """Redirects user to the correct dashboard based on their role."""
    if request.user.role == "customer":
        return redirect("customer_dashboard")
    elif request.user.role == "merchant":
        return redirect("merchant_dashboard")
    else:
        return redirect("admin:index")  # Default for superusers




### ** User Profile View**
class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = "users/user_detail.html"
    context_object_name = "user"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Fetch the correct profile data based on the user's role
        if self.object.role == "customer":
            context["profile"] = get_object_or_404(Customer, user=self.object)
            context["profile_type"] = "customer"
        elif self.object.role == "merchant":
            context["profile"] = get_object_or_404(Merchant, user=self.object)
            context["profile_type"] = "merchant"
        
        return context

user_detail_view = UserDetailView.as_view()





### ** Customer Profile View**
class CustomerDetailView(LoginRequiredMixin, CustomerOnlyMixin,  DetailView):
    """Customer profile view."""
    model = Customer
    template_name = "customers/customer_detail.html"

    def get_object(self, queryset: QuerySet | None = None) -> Customer:
        return get_object_or_404(Customer, user__pk=self.kwargs["pk"])


customer_detail_view = CustomerDetailView.as_view()


### ** Merchant Profile View**
class MerchantDetailView(LoginRequiredMixin, MerchantOnlyMixin, DetailView):
    """Merchant profile view."""
    model = Merchant
    template_name = "merchants/merchant_detail.html"

    def get_object(self, queryset: QuerySet | None = None) -> Merchant:
        return get_object_or_404(Merchant, user__pk=self.kwargs["pk"])


merchant_detail_view = MerchantDetailView.as_view()



class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    fields = []
    success_message = _("Information successfully updated")

    def get_success_url(self) -> str:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user.get_absolute_url()

    def get_object(self, queryset: QuerySet | None=None) -> User:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user


user_update_view = UserUpdateView.as_view()


### ** Customer Update View**
class CustomerUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """Allows customers to update their profile info."""
    model = Customer
    fields = ["first_name", "last_name", "phone", "address"]
    form_class = CustomerForm
    template_name = "customers/customer_form.html"  # Explicitly set correct template
    success_message = _("Customer information successfully updated")

    def get_success_url(self) -> str:
        return self.request.user.get_absolute_url()

    def get_object(self, queryset: QuerySet | None = None) -> Customer:
        return get_object_or_404(Customer, user=self.request.user)


customer_update_view = CustomerUpdateView.as_view()


### ** Merchant Update View**
class MerchantUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """Allows merchants to update their business details."""
    model = Merchant
    fields = ["company_name", "phone", "address"]
    form_class = MerchantForm
    template_name = "merchants/merchant_form.html"  # Explicitly set correct template
    
    success_message = _("Merchant information successfully updated")

    def get_success_url(self) -> str:
        return self.request.user.get_absolute_url()

    def get_object(self, queryset: QuerySet | None = None) -> Merchant:
        return get_object_or_404(Merchant, user=self.request.user)


merchant_update_view = MerchantUpdateView.as_view()


### ** Role-Based Redirect View**
class UserRedirectView(LoginRequiredMixin, RedirectView):
    """Redirects user to the correct profile based on role."""
    permanent = False

    def get_redirect_url(self) -> str:
        if self.request.user.role == "customer":
            return reverse("users:customer_detail", kwargs={"pk": self.request.user.pk})
        elif self.request.user.role == "merchant":
            return reverse("users:merchant_detail", kwargs={"pk": self.request.user.pk})
        return reverse("users:detail", kwargs={"pk": self.request.user.pk})


user_redirect_view = UserRedirectView.as_view()


