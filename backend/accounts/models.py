from django.contrib.auth.models import AbstractUser, UserManager as BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Custom user manager for CloudDeploy User model."""

    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", User.Role.DEVELOPER)
        return super().create_user(username, email=email, password=password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return super().create_superuser(username, email=email, password=password, **extra_fields)


class User(AbstractUser):
    """
    Custom user model for CloudDeploy extending Django's AbstractUser.
    Includes role-based access control with ADMIN and DEVELOPER roles.
    """

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        DEVELOPER = "DEVELOPER", "Developer"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.DEVELOPER,
        help_text="Designates the user's role within CloudDeploy.",
    )

    objects = UserManager()

    @property
    def is_admin_role(self) -> bool:
        """Returns True if the user has an ADMIN role or is a superuser."""
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_developer_role(self) -> bool:
        """Returns True if the user has a DEVELOPER role."""
        return self.role == self.Role.DEVELOPER

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
