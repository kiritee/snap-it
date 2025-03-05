from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied



### **🔹 Role Checking Functions**
def is_customer(user):
    """Checks if the user is a customer."""
    return user.is_authenticated and user.role == "customer"

def is_merchant(user):
    """Checks if the user is a merchant."""
    return user.is_authenticated and user.role == "merchant"

def is_admin(user):
    """Checks if the user is an admin (superuser)."""
    return user.is_authenticated and user.is_superuser


### **🔹 Django View Decorators (For Normal Views)**
def customer_required(view_func):
    """Decorator to restrict access to customers only."""
    def _wrapped_view(request, *args, **kwargs):
        if not is_customer(request.user):
            raise PermissionDenied  # Returns 403 instead of redirecting
        return view_func(request, *args, **kwargs)
    return login_required(_wrapped_view)

def merchant_required(view_func):
    """Decorator to restrict access to merchants only."""
    def _wrapped_view(request, *args, **kwargs):
        if not is_merchant(request.user):
            raise PermissionDenied  # Returns 403 instead of redirecting
        return view_func(request, *args, **kwargs)
    return login_required(_wrapped_view)

def admin_required(view_func):
    """Decorator to restrict access to admins only."""
    def _wrapped_view(request, *args, **kwargs):
        if not is_admin(request.user):
            raise PermissionDenied  # Returns 403 instead of redirecting
        return view_func(request, *args, **kwargs)
    return login_required(_wrapped_view)


