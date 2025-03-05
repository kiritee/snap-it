from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Customize JWT payload to include role and user ID."""
    
    def validate(self, attrs):
        data = super().validate(attrs)

        # Add extra claims (role, user ID)
        data["user_id"] = self.user.id
        data["role"] = self.user.role

        return data