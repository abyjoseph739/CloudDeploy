import uuid
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
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


class ApplicationAPITests(TestCase):
    """Tests for the Application REST endpoints, scoping, and permissions."""

    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            username="admin_user",
            email="admin@example.com",
            password="AdminPass123!",
            role=User.Role.ADMIN,
        )
        self.dev1 = User.objects.create_user(
            username="dev1",
            email="dev1@example.com",
            password="Dev1Pass123!",
            role=User.Role.DEVELOPER,
        )
        self.dev2 = User.objects.create_user(
            username="dev2",
            email="dev2@example.com",
            password="Dev2Pass123!",
            role=User.Role.DEVELOPER,
        )

        self.app1 = Application.objects.create(
            name="App One",
            description="First application",
            github_repo_url="https://github.com/clouddeploy/app-one",
            default_branch="main",
            created_by=self.dev1,
            is_active=True,
        )
        self.app2 = Application.objects.create(
            name="App Two",
            description="Second application",
            github_repo_url="https://github.com/clouddeploy/app-two",
            default_branch="master",
            created_by=self.dev2,
            is_active=True,
        )

    def test_unauthenticated_access_denied(self):
        """Unauthenticated requests are denied access."""
        response = self.client.get("/api/applications/")
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_developer_lists_only_own_applications(self):
        """Developers only see applications they created."""
        self.client.force_authenticate(user=self.dev1)
        response = self.client.get("/api/applications/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json().get("results", response.json())
        names = [item["name"] for item in results]
        self.assertIn("App One", names)
        self.assertNotIn("App Two", names)

    def test_admin_lists_all_applications(self):
        """Admins can view all applications in the system."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get("/api/applications/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json().get("results", response.json())
        names = [item["name"] for item in results]
        self.assertIn("App One", names)
        self.assertIn("App Two", names)

    def test_create_application(self):
        """Creating an application automatically binds created_by to authenticated user."""
        self.client.force_authenticate(user=self.dev1)
        payload = {
            "name": "New Spice App",
            "description": "Spices shop",
            "github_repo_url": "https://github.com/spices/shop",
            "default_branch": "main",
        }
        response = self.client.post("/api/applications/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data["name"], "New Spice App")
        self.assertEqual(data["created_by"], self.dev1.id)
        self.assertTrue(data["is_active"])

    def test_create_application_invalid_url(self):
        """Invalid repository URLs fail validation with 400."""
        self.client.force_authenticate(user=self.dev1)
        payload = {
            "name": "Bad URL App",
            "github_repo_url": "not-a-valid-url",
        }
        response = self.client.post("/api/applications/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("github_repo_url", response.json())

    def test_retrieve_application_authorized(self):
        """Owner can retrieve application details."""
        self.client.force_authenticate(user=self.dev1)
        response = self.client.get(f"/api/applications/{self.app1.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["name"], "App One")

    def test_retrieve_application_unauthorized(self):
        """Developers cannot retrieve applications created by other developers."""
        self.client.force_authenticate(user=self.dev2)
        response = self.client.get(f"/api/applications/{self.app1.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_application_owner(self):
        """Owner can update editable fields of their application."""
        self.client.force_authenticate(user=self.dev1)
        payload = {
            "description": "Updated description for App One",
            "default_branch": "develop",
        }
        response = self.client.patch(f"/api/applications/{self.app1.id}/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.app1.refresh_from_db()
        self.assertEqual(self.app1.description, "Updated description for App One")
        self.assertEqual(self.app1.default_branch, "develop")

    def test_update_protected_fields_immutable(self):
        """Protected fields like created_by, is_active, and id cannot be changed via PATCH."""
        self.client.force_authenticate(user=self.dev1)
        original_created_by = self.app1.created_by
        payload = {
            "created_by": self.dev2.id,
            "is_active": False,
        }
        response = self.client.patch(f"/api/applications/{self.app1.id}/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.app1.refresh_from_db()
        self.assertEqual(self.app1.created_by, original_created_by)
        self.assertTrue(self.app1.is_active)

    def test_deactivate_application_owner(self):
        """Owner can deactivate their application."""
        self.client.force_authenticate(user=self.dev1)
        response = self.client.post(f"/api/applications/{self.app1.id}/deactivate/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.app1.refresh_from_db()
        self.assertFalse(self.app1.is_active)

    def test_deactivate_application_unauthorized(self):
        """Another developer cannot deactivate someone else's application."""
        self.client.force_authenticate(user=self.dev2)
        response = self.client.post(f"/api/applications/{self.app1.id}/deactivate/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.app1.refresh_from_db()
        self.assertTrue(self.app1.is_active)

    def test_deactivate_application_admin(self):
        """Admins can deactivate any application."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f"/api/applications/{self.app1.id}/deactivate/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.app1.refresh_from_db()
        self.assertFalse(self.app1.is_active)

    def test_application_summary(self):
        """Summary endpoint returns correct aggregated stats."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get("/api/applications/summary/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["total_applications"], 2)
        self.assertEqual(data["active_applications"], 2)
        self.assertEqual(data["inactive_applications"], 0)
