from django.contrib.auth import update_session_auth_hash
from django.core.mail import send_mail
from django.template.loader import render_to_string
from rest_framework import status, generics
from rest_framework.decorators import action
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin, ListModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.generics import RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from django.contrib.auth.password_validation import validate_password

from snap_it.users.models import User, Customer, Merchant
from .serializers import UserSerializer, CustomerSerializer, MerchantSerializer, PasswordChangeSerializer
from .permissions import IsCustomer, IsMerchant, IsAdminUser



### **🔹 User API ViewSet**
class UserViewSet(RetrieveModelMixin, ListModelMixin, UpdateModelMixin, GenericViewSet):
    """ViewSet for managing User profiles."""
    serializer_class = UserSerializer
    queryset = User.objects.all()
    lookup_field = "pk"
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Restrict users to only see their own profile."""
        return self.queryset.filter(id=self.request.user.id)

    @action(detail=False, methods=["get"])
    def me(self, request):
        """Returns the current authenticated user's profile."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


### **🔹 Customer API ViewSet**
class CustomerViewSet(RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    """ViewSet for retrieving and updating Customer profiles."""
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated, IsCustomer]

    def get_object(self):
        return get_object_or_404(Customer, user=self.request.user)


### **🔹 Merchant API ViewSet**
class MerchantViewSet(RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    """ViewSet for retrieving and updating Merchant profiles."""
    serializer_class = MerchantSerializer
    permission_classes = [IsAuthenticated, IsMerchant]

    def get_object(self):
        return get_object_or_404(Merchant, user=self.request.user)


### **🔹 Get User Profile**
class UserDetailAPI(RetrieveAPIView):
    """API for retrieving user profile (basic details)."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


### **🔹 Get Customer Profile**
class CustomerDetailAPI(RetrieveAPIView):
    """API for retrieving customer profile."""
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated, IsCustomer]

    def get_object(self):
        return get_object_or_404(Customer, user=self.request.user)


### **🔹 Get Merchant Profile**
class MerchantDetailAPI(RetrieveAPIView):
    """API for retrieving merchant profile."""
    serializer_class = MerchantSerializer
    permission_classes = [IsAuthenticated, IsMerchant]

    def get_object(self):
        return get_object_or_404(Merchant, user=self.request.user)


### **🔹 Update Customer Profile**
class CustomerUpdateAPI(UpdateAPIView):
    """API for updating customer profile."""
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated, IsCustomer]

    def get_object(self):
        return get_object_or_404(Customer, user=self.request.user)


### **🔹 Update Merchant Profile**
class MerchantUpdateAPI(UpdateAPIView):
    """API for updating merchant profile."""
    serializer_class = MerchantSerializer
    permission_classes = [IsAuthenticated, IsMerchant]

    def get_object(self):
        return get_object_or_404(Merchant, user=self.request.user)
    

class PasswordChangeView(generics.UpdateAPIView):
    """
    API for changing user password and forcing logout from all sessions.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PasswordChangeSerializer

    def update(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Change password
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        # Invalidate the session to log the user out
        update_session_auth_hash(request, user)

        # Blacklist all outstanding tokens (logout from all devices)
        tokens = OutstandingToken.objects.filter(user=user)
        for token in tokens:
            token.blacklist()

        # Send Email Notification
        subject = _("Password Changed Successfully")
        message = _("""Hello,

Your password has been changed successfully. 

If you did not request this change, please reset your password immediately or contact support.

Thank you,
Snap-It Team""")
        


        html_message = render_to_string("emails/password_changed.html", {"user": user})
        send_mail(
            subject,
            message,
            "Snap-It! <konark@gmail.com>",
            [user.email],
            fail_silently=False,
            html_message=html_message,
        )


        return Response({"message": "Password changed. All sessions logged out."}, status=status.HTTP_200_OK)

