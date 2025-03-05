from rest_framework.permissions import BasePermission
from django.core.cache import cache
from rest_framework_simplejwt.authentication import JWTAuthentication

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


### **🔹 Django REST Framework Permissions (For API Views)**
class IsCustomer(BasePermission):
    """Allows access only to customers."""
    def has_permission(self, request, view):
        return is_customer(request.user)

class IsMerchant(BasePermission):
    """Allows access only to merchants."""
    def has_permission(self, request, view):
        return is_merchant(request.user)

class IsAdminUser(BasePermission):
    """Allows access only to Django superusers."""
    def has_permission(self, request, view):
        return is_admin(request.user)


class CustomJWTAuthentication(JWTAuthentication):
    """Rejects access tokens if the user has logged out."""
    
    def authenticate(self, request):
        authentication = super().authenticate(request)
        if authentication is None:
            return None

        user, token = authentication
        if cache.get(f"user_logout_{user.id}") == "logout":
            return None  # Reject this token (force logout)
        return user, token