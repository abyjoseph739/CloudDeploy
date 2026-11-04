from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Safe serializer for user profile data; excludes credentials and hashes."""

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_staff",
            "is_superuser",
            "date_joined",
        ]
        read_only_fields = fields


class LoginSerializer(serializers.Serializer):
    """Serializer validating incoming login requests."""

    username = serializers.CharField(required=True, trim_whitespace=True)
    password = serializers.CharField(required=True, write_only=True)

