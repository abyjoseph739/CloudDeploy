from django.contrib import admin
from .models import Deployment


@admin.register(Deployment)
class DeploymentAdmin(admin.ModelAdmin):
    """Admin configuration for Deployment model."""

    list_display = (
        "id",
        "application",
        "environment",
        "status",
        "requested_by",
        "commit_hash",
        "created_at",
        "completed_at",
    )
    list_filter = ("status", "environment", "created_at")
    search_fields = ("id", "application__name", "commit_hash", "error_summary")
    readonly_fields = ("id", "created_at", "started_at", "completed_at")
    ordering = ("-created_at",)
