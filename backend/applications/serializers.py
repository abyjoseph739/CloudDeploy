from urllib.parse import urlparse
from rest_framework import serializers
from .models import Application


class ApplicationSerializer(serializers.ModelSerializer):
    """
    Serializer for the Application model.
    Includes creator metadata and validates repository URLs and branch names.
    Protected fields are strictly read-only.
    """

    created_by_username = serializers.SerializerMethodField(read_only=True)
    created_by_role = serializers.SerializerMethodField(read_only=True)
    deployments_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Application
        fields = [
            "id",
            "name",
            "description",
            "github_repo_url",
            "default_branch",
            "created_by",
            "created_by_username",
            "created_by_role",
            "is_active",
            "created_at",
            "updated_at",
            "deployments_count",
        ]
        read_only_fields = [
            "id",
            "created_by",
            "created_by_username",
            "created_by_role",
            "is_active",
            "created_at",
            "updated_at",
            "deployments_count",
        ]

    def get_created_by_username(self, obj):
        return obj.created_by.username if obj.created_by else None

    def get_created_by_role(self, obj):
        return obj.created_by.role if obj.created_by else None

    def get_deployments_count(self, obj):
        return obj.deployments.count()

    def validate_name(self, value):
        stripped = value.strip()
        if len(stripped) < 2:
            raise serializers.ValidationError("Application name must be at least 2 characters long.")
        return stripped

    def validate_default_branch(self, value):
        stripped = value.strip()
        if not stripped:
            return "main"
        if " " in stripped:
            raise serializers.ValidationError("Branch name cannot contain spaces.")
        return stripped

    def validate_github_repo_url(self, value):
        stripped = value.strip()
        parsed = urlparse(stripped)
        if parsed.scheme not in ("http", "https"):
            raise serializers.ValidationError("Repository URL must begin with http:// or https://.")
        if not parsed.netloc:
            raise serializers.ValidationError("Please provide a valid repository URL.")
        return stripped

