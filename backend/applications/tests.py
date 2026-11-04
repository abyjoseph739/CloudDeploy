import uuid
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from applications.models import Application

User = get_user_model()


class ApplicationModelTests(TestCase):
    """Tests for the Application model in the applications app."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="appdev",
            email="dev@example.com",
            password="AppDevPassword123!",
        )

    def test_application_creation_with_defaults(self):
        """Application should be created with correct default fields and a unique UUID."""
        app = Application.objects.create(
            name="Spices E-Commerce",
            description="Online spices shopping platform with cloud deployment pipeline.",
            github_repo_url="https://github.com/clouddeploy-demo/spices-shop",
            created_by=self.user,
        )

        self.assertIsInstance(app.id, uuid.UUID)
        self.assertEqual(app.name, "Spices E-Commerce")
        self.assertEqual(app.default_branch, "main")
        self.assertTrue(app.is_active)
        self.assertEqual(app.created_by, self.user)
        self.assertIsNotNone(app.created_at)
        self.assertIsNotNone(app.updated_at)
        self.assertEqual(str(app), "Spices E-Commerce")

    def test_application_custom_branch_and_inactive(self):
        """Application can be created with a custom default branch and inactive status."""
        app = Application.objects.create(
            name="Analytics Service",
            github_repo_url="https://github.com/clouddeploy-demo/analytics",
            default_branch="develop",
            is_active=False,
        )
        self.assertEqual(app.default_branch, "develop")
        self.assertFalse(app.is_active)
        self.assertIsNone(app.created_by)

    def test_application_name_unique_constraint(self):
        """Application name must be unique."""
        Application.objects.create(
            name="Duplicate App",
            github_repo_url="https://github.com/clouddeploy-demo/app1",
        )
        with self.assertRaises(IntegrityError):
            Application.objects.create(
                name="Duplicate App",
                github_repo_url="https://github.com/clouddeploy-demo/app2",
            )
