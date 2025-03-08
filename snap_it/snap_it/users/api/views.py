from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.template.loader import render_to_string
from rest_framework import status, generics
from rest_framework.decorators import action
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin, ListModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework.generics import RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from django.contrib.auth.password_validation import validate_password

from snap_it.users.models import User, Customer, Merchant
from .serializers import UserSerializer, CustomerSerializer, MerchantSerializer, PasswordChangeSerializer
from .permissions import IsCustomer, IsMerchant, IsAdminUser


class UserViewSet(ModelViewSet):
    """API for managing users."""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "pk"
    queryset = User.objects.all()
    http_method_names = ["get", "patch", "delete", "options", "put"]  # Prevent `POST` (creation)

    def get_queryset(self):
        """Restrict users to only see their own profile."""
        return self.queryset.filter(id=self.request.user.id)


    def get_object(self):
        """Ensure users can only retrieve their own profile."""
        return self.request.user  # Forces user to access only their own data


    def destroy(self, request, *args, **kwargs):
        """Soft delete user instead of removing from database."""
        user = self.request.user
        user.is_active = False  #  Mark user as inactive
        user.save()
        return Response({"message": "Account deactivated successfully."}, status=status.HTTP_204_NO_CONTENT)
    

    @action(detail=False, methods=["get", "patch", "put", "delete","options"])
    def me(self, request):
        """Retrieve, update, or deactivate the current authenticated user's profile."""
        user = request.user  # Get the logged-in user

        # PATCH: Partially update user profile
        if request.method == "PATCH":
            serializer = self.get_serializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        # ✅ PUT: Fully update user profile (requires all fields)
        elif request.method == "PUT":
            serializer = self.get_serializer(user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        # ✅ DELETE: Soft delete user (deactivate account)
        elif request.method == "DELETE":
            user.is_active = False  # Mark user as inactive
            user.save()
            return Response({"message": "User account deactivated successfully."}, status=status.HTTP_204_NO_CONTENT)

        # ✅ Default GET behavior
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    




class CustomerViewSet(ModelViewSet):
    """ViewSet for Customer model (Read, Update, Soft Delete Only)."""
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated, IsCustomer]
    queryset = Customer.objects.filter(user__is_active=True)  # ✅ Only return active customers
    http_method_names = ["get", "patch", "delete", "options", "put"]   # 🚫 Prevent `POST` (creation)

    def get_queryset(self):
        """Restrict users to only see their own profile."""
        return self.queryset.filter(user=self.request.user)


    def get_object(self):
        return get_object_or_404(Customer, user=self.request.user)


    def destroy(self, request, *args, **kwargs):
        """Soft-delete customer: Deactivate Customer and User instead of deleting."""
        customer = self.get_object()
        customer.is_active = False  #  Deactivate customer
        customer.user.is_active = False  # Deactivate user
        customer.save()
        customer.user.save()
        return Response({"message": "Customer deactivated successfully."}, status=status.HTTP_204_NO_CONTENT)
    

    @action(detail=False, methods=["get", "patch", "put", "delete"])
    def me(self, request):
        """Retrieve, update, or deactivate the current authenticated customer's profile."""
        customer = get_object_or_404(Customer, user=request.user)

        # PATCH: Partially update customer profile
        if request.method == "PATCH":
            serializer = self.get_serializer(customer, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        # PUT: Fully update customer profile (requires all fields)
        elif request.method == "PUT":
            serializer = self.get_serializer(customer, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        # DELETE: Soft delete customer (deactivate account)
        elif request.method == "DELETE":
            customer.is_active = False  # Deactivate customer
            customer.user.is_active = False  # Deactivate user
            customer.save()
            customer.user.save()
            return Response({"message": "Customer account deactivated successfully."}, status=status.HTTP_204_NO_CONTENT)

        # Default GET behavior
        serializer = self.get_serializer(customer)
        return Response(serializer.data, status=status.HTTP_200_OK)




class MerchantViewSet(ModelViewSet):
    """ViewSet for Merchant model (Read, Update, Soft Delete Only)."""
    serializer_class = MerchantSerializer
    permission_classes = [IsAuthenticated, IsMerchant]
    queryset = Merchant.objects.filter(user__is_active=True)  # ✅ Only return active merchants
    http_method_names = ["get", "patch", "delete", "options", "put"]   # 🚫 Prevent `POST` (creation)

    def get_queryset(self):
        """Restrict users to only see their own profile."""
        return self.queryset.filter(user=self.request.user)


    def get_object(self):
        return get_object_or_404(Merchant, user=self.request.user)


    def destroy(self, request, *args, **kwargs):
        """Soft-delete merchant: Deactivate Merchant and User instead of deleting."""
        merchant = self.get_object()
        merchant.is_active = False  #  Deactivate merchant
        merchant.user.is_active = False  # Deactivate user
        merchant.save()
        merchant.user.save()
        return Response({"message": "Merchant deactivated successfully."}, status=status.HTTP_204_NO_CONTENT)
    

    @action(detail=False, methods=["get", "patch", "put", "delete"])
    def me(self, request):
        """Retrieve, update, or deactivate the current authenticated merchant's profile."""
        merchant = get_object_or_404(Merchant, user=request.user)

        # PATCH: Partially update merchant profile
        if request.method == "PATCH":
            serializer = self.get_serializer(merchant, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        # PUT: Fully update merchant profile (requires all fields)
        elif request.method == "PUT":
            serializer = self.get_serializer(merchant, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        # DELETE: Soft delete merchant (deactivate account)
        elif request.method == "DELETE":
            merchant.is_active = False  # Deactivate merchant
            merchant.user.is_active = False  # Deactivate user
            merchant.save()
            merchant.user.save()
            return Response({"message": "Merchant account deactivated successfully."}, status=status.HTTP_204_NO_CONTENT)

        # Default GET behavior
        serializer = self.get_serializer(merchant)
        return Response(serializer.data, status=status.HTTP_200_OK)

    


class UserRegistrationView(generics.CreateAPIView):
    """API endpoint for user registration."""
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        """Ensure password is hashed before creating a user."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(password=make_password(serializer.validated_data["password"]))
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    



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

