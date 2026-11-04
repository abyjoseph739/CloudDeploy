import uuid
from django.conf import settings
from django.db import models
from applications.models import Application


class Deployment(models.Model):
    """
    Represents a deployment job/event for an application within CloudDeploy.
    Tracks status, environment, target commit SHA, and execution timestamps.
    """

    class Environment(models.TextChoices):
        DEVELOPMENT = "DEVELOPMENT", "Development"
        STAGING = "STAGING", "Staging"
        PRODUCTION = "PRODUCTION", "Production"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        QUEUED = "QUEUED", "Queued"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"
        CANCELLED = "CANCELLED", "Cancelled"
        ROLLED_BACK = "ROLLED_BACK", "Rolled Back"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the deployment.",
    )
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="deployments",
        help_text="The application to which this deployment belongs.",
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deployments",
        help_text="User who initiated this deployment.",
    )
    commit_hash = models.CharField(
        max_length=40,
        blank=True,
        null=True,
        help_text="Git commit SHA being deployed (nullable initially).",
    )
    environment = models.CharField(
        max_length=20,
        choices=Environment.choices,
        default=Environment.PRODUCTION,
        help_text="Target deployment environment.",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        help_text="Current state of the deployment.",
    )
    error_summary = models.TextField(
        blank=True,
        null=True,
        help_text="Summary of errors if the deployment failed.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Timestamp when deployment was requested.",
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when deployment execution started.",
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when deployment completed.",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Deployment"
        verbose_name_plural = "Deployments"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["application", "environment"]),
        ]

    def __str__(self):
        return f"{self.application.name} [{self.environment}] - {self.status} ({self.id})"
