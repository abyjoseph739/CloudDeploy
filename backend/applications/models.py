import uuid
from django.conf import settings
from django.db import models


class Application(models.Model):
    """
    Represents an application registered in CloudDeploy.
    Stores metadata including the GitHub repository URL and default deployment branch.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the application.",
    )
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Unique name of the application (e.g. Spices E-Commerce).",
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Detailed description of the application.",
    )
    github_repo_url = models.URLField(
        max_length=500,
        help_text="URL of the GitHub repository (e.g. https://github.com/organization/spices-shop).",
    )
    default_branch = models.CharField(
        max_length=100,
        default="main",
        help_text="Default git branch used for deployments (e.g. main, master).",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="applications",
        help_text="User who registered this application.",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Indicates if the application is active and deployable.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Timestamp when the application was registered.",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when the application metadata was last updated.",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Application"
        verbose_name_plural = "Applications"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return self.name
