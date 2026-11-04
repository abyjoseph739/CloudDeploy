import uuid
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from applications.models import Application
from deployments.models import Deployment

User = get_user_model()


class DeploymentModelTests(TestCase):
    """Tests for the Deployment model in the deployments app."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="deployer",
            email="deployer@example.com",
            password="DeployPassword123!",
        )
        self.application = Application.objects.create(
            name="Spices E-Commerce",
            github_repo_url="https://github.com/clouddeploy-demo/spices-shop",
            created_by=self.user,
        )

    def test_deployment_creation_with_defaults(self):
        """Deployment should be created with correct defaults, UUID, and initial status."""
        deployment = Deployment.objects.create(
            application=self.application,
            requested_by=self.user,
        )

        self.assertIsInstance(deployment.id, uuid.UUID)
        self.assertEqual(deployment.application, self.application)
        self.assertEqual(deployment.requested_by, self.user)
        self.assertEqual(deployment.status, Deployment.Status.PENDING)
        self.assertEqual(deployment.environment, Deployment.Environment.PRODUCTION)
        self.assertIsNone(deployment.commit_hash)
        self.assertIsNone(deployment.error_summary)
        self.assertIsNone(deployment.started_at)
        self.assertIsNone(deployment.completed_at)
        self.assertIsNotNone(deployment.created_at)

        expected_str = f"Spices E-Commerce [PRODUCTION] - PENDING ({deployment.id})"
        self.assertEqual(str(deployment), expected_str)

    def test_deployment_full_lifecycle_fields(self):
        """Deployment can be updated with commit hash, execution timestamps, and success status."""
        now = timezone.now()
        deployment = Deployment.objects.create(
            application=self.application,
            requested_by=self.user,
            commit_hash="a1b2c3d4e5f6789012345678901234567890abcd",
            environment=Deployment.Environment.STAGING,
            status=Deployment.Status.SUCCESS,
            started_at=now,
            completed_at=now,
        )

        self.assertEqual(deployment.commit_hash, "a1b2c3d4e5f6789012345678901234567890abcd")
        self.assertEqual(deployment.environment, Deployment.Environment.STAGING)
        self.assertEqual(deployment.status, Deployment.Status.SUCCESS)
        self.assertEqual(deployment.started_at, now)
        self.assertEqual(deployment.completed_at, now)

    def test_deployment_failed_with_error_summary(self):
        """Deployment records error summary upon failure."""
        deployment = Deployment.objects.create(
            application=self.application,
            requested_by=self.user,
            status=Deployment.Status.FAILED,
            error_summary="Build failed: syntax error in configuration file.",
        )
        self.assertEqual(deployment.status, Deployment.Status.FAILED)
        self.assertEqual(
            deployment.error_summary,
            "Build failed: syntax error in configuration file.",
        )

    def test_application_and_deployment_relationship(self):
        """Application should be able to query its associated deployments via related_name."""
        dep1 = Deployment.objects.create(
            application=self.application,
            requested_by=self.user,
            environment=Deployment.Environment.DEVELOPMENT,
        )
        dep2 = Deployment.objects.create(
            application=self.application,
            requested_by=self.user,
            environment=Deployment.Environment.PRODUCTION,
        )

        app_deployments = self.application.deployments.all()
        self.assertEqual(app_deployments.count(), 2)
        self.assertIn(dep1, app_deployments)
        self.assertIn(dep2, app_deployments)

    def test_environment_and_status_choices(self):
        """Environment and status choices should include all required states."""
        env_choices = [c[0] for c in Deployment.Environment.choices]
        self.assertIn("DEVELOPMENT", env_choices)
        self.assertIn("STAGING", env_choices)
        self.assertIn("PRODUCTION", env_choices)

        status_choices = [c[0] for c in Deployment.Status.choices]
        self.assertIn("PENDING", status_choices)
        self.assertIn("QUEUED", status_choices)
        self.assertIn("IN_PROGRESS", status_choices)
        self.assertIn("SUCCESS", status_choices)
        self.assertIn("FAILED", status_choices)
        self.assertIn("CANCELLED", status_choices)
        self.assertIn("ROLLED_BACK", status_choices)
