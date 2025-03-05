from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from snap_it.users.models import User, Customer, Merchant

class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    class Meta:
        model = User
        fields = ["id", "email", "role", "is_staff", "is_superuser"]

class CustomerSerializer(serializers.ModelSerializer):
    """Serializer for Customer model."""
    user = UserSerializer(read_only=True)

    class Meta:
        model = Customer
        fields = ["user", "first_name", "last_name", "phone", "address"]

class MerchantSerializer(serializers.ModelSerializer):
    """Serializer for Merchant model."""
    user = UserSerializer(read_only=True)

    class Meta:
        model = Merchant
        fields = ["user", "company_name", "phone", "address"]




class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        """Ensure old password is correct."""
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def validate_new_password(self, value):
        """Ensure new password meets Django's security requirements."""
        validate_password(value)
        return value

