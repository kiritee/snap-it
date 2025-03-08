from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from snap_it.users.models import User, Customer, Merchant


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model with auto customer/merchant creation and role update handling."""
    password = serializers.CharField(write_only=True, required=True)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, default="customer")

    class Meta:
        model = User
        fields = ["id", "email", "password", "role", "is_staff", "is_superuser"]


    def create(self, validated_data):
        """Ensure password is hashed before saving and create Customer/Merchant based on role."""
        validated_data["password"] = make_password(validated_data["password"])  
        user = super().create(validated_data)  

        # Auto-create Customer or Merchant based on role
        if user.role == "customer":
            Customer.objects.create(user=user)  
        elif user.role == "merchant":
            Merchant.objects.create(user=user)  

        return user  


    def update(self, instance, validated_data):
        """Prevent password updates via UserSerializer."""
        if "password" in validated_data:
            validated_data.pop("password")  # Remove password from validated_data

        # Handle Role Change Logic
        new_role = validated_data.get("role", instance.role)

        if new_role != instance.role:  # Only process if role actually changes
            if new_role == "customer":
                # Deactivate existing Merchant profile (if exists)
                Merchant.objects.filter(user=instance).update(is_active=False)
                # Create new Customer profile
                Customer.objects.create(user=instance)

            elif new_role == "merchant":
                # Deactivate existing Customer profile (if exists)
                Customer.objects.filter(user=instance).update(is_active=False)
                # Create new Merchant profile
                Merchant.objects.create(user=instance)

        return super().update(instance, validated_data)

    
    def validate_password(self, value):
        """Ensure password meets security requirements."""
        validate_password(value)  # ✅ Uses Django's built-in password validation
        return value




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

