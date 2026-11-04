from django.contrib import admin
from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    """Admin configuration for Application model."""

    list_display = (
        "name",
        "default_branch",
        "is_active",
        "created_by",
        "created_at",
        "updated_at",
    )
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "github_repo_url", "description")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-created_at",)
