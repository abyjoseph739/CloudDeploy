from django.contrib.auth import authenticate, get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


class CustomUserModelTests(TestCase):
    """Tests for the custom CloudDeploy User model, role choices, and authentication."""

    def test_create_user_with_default_role(self):
        """A user created without specifying a role should default to DEVELOPER."""
        user = User.objects.create_user(
            username="developer1",
            email="dev1@example.com",
            password="SecurePassword123!",
        )
        self.assertEqual(user.role, User.Role.DEVELOPER)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_developer_role)
        self.assertFalse(user.is_admin_role)
        self.assertEqual(str(user), "developer1 (Developer)")

    def test_create_user_with_admin_role(self):
        """A user can be explicitly created with the ADMIN role."""
        user = User.objects.create_user(
            username="admin1",
            email="admin1@example.com",
            password="SecurePassword123!",
            role=User.Role.ADMIN,
        )
        self.assertEqual(user.role, User.Role.ADMIN)
        self.assertTrue(user.is_admin_role)
        self.assertFalse(user.is_developer_role)
        self.assertEqual(str(user), "admin1 (Admin)")

    def test_password_hashing_and_authentication(self):
        """Passwords should be properly hashed and verified via Django's auth backend."""
        raw_password = "MyComplexPassword2026!"
        user = User.objects.create_user(
            username="testauth",
            email="auth@example.com",
            password=raw_password,
        )
        self.assertNotEqual(user.password, raw_password)
        self.assertTrue(user.check_password(raw_password))
        self.assertFalse(user.check_password("WrongPassword!"))

        authenticated_user = authenticate(username="testauth", password=raw_password)
        self.assertIsNotNone(authenticated_user)
        self.assertEqual(authenticated_user.id, user.id)

        failed_user = authenticate(username="testauth", password="WrongPassword!")
        self.assertIsNone(failed_user)

    def test_create_superuser(self):
        """Creating a superuser sets is_staff=True, is_superuser=True, and role=ADMIN by default."""
        superuser = User.objects.create_superuser(
            username="superadmin",
            email="super@example.com",
            password="SuperPassword123!",
        )
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
        self.assertEqual(superuser.role, User.Role.ADMIN)
        self.assertTrue(superuser.is_admin_role)

    def test_role_choices(self):
        """Role field must support ADMIN and DEVELOPER choices."""
        valid_roles = [choice[0] for choice in User.Role.choices]
        self.assertIn("ADMIN", valid_roles)
        self.assertIn("DEVELOPER", valid_roles)


class AuthAPITests(TestCase):
    """Tests for the Authentication APIs (CSRF, login, logout, me)."""

    def setUp(self):
        self.client = APIClient()
        self.password = "ValidDevPass123!"
        self.user = User.objects.create_user(
            username="devuser",
            email="devuser@example.com",
            password=self.password,
            role=User.Role.DEVELOPER,
        )

    def test_csrf_token_endpoint(self):
        """GET /api/auth/csrf/ returns 200, sets csrftoken cookie, and provides token."""
        response = self.client.get("/api/auth/csrf/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("csrfToken", data)
        self.assertTrue(len(data["csrfToken"]) > 10)
        self.assertIn("csrftoken", response.cookies)

    def test_login_success(self):
        """POST /api/auth/login/ with valid credentials returns 200 and safe user details."""
        response = self.client.post(
            "/api/auth/login/",
            {"username": "devuser", "password": self.password},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data.get("detail"), "Login successful.")
        user_info = data.get("user")
        self.assertIsNotNone(user_info)
        self.assertEqual(user_info["username"], "devuser")
        self.assertEqual(user_info["role"], User.Role.DEVELOPER)
        self.assertNotIn("password", user_info)
        # Verify fresh post-login CSRF token is provided
        self.assertIn("csrfToken", data)

    def test_login_invalid_password(self):
        """POST /api/auth/login/ with invalid credentials returns 401."""
        response = self.client.post(
            "/api/auth/login/",
            {"username": "devuser", "password": "WrongPassword999!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.json())

    def test_login_inactive_user(self):
        """Inactive accounts cannot log in."""
        self.user.is_active = False
        self.user.save()

        response = self.client.post(
            "/api/auth/login/",
            {"username": "devuser", "password": self.password},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.json())

    def test_login_missing_fields(self):
        """Missing username or password returns 400 validation error."""
        response = self.client.post("/api/auth/login/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_current_user_unauthenticated(self):
        """GET /api/auth/me/ returns 401 for unauthenticated clients."""
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_current_user_authenticated(self):
        """GET /api/auth/me/ returns user profile when logged in."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["username"], "devuser")
        self.assertEqual(data["role"], User.Role.DEVELOPER)
        self.assertNotIn("password", data)

    def test_logout(self):
        """POST /api/auth/logout/ successfully logs out user and rotates CSRF token."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/api/auth/logout/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get("detail"), "Successfully logged out.")
        self.assertIn("csrfToken", response.json())


class CSRFRegressionTests(TestCase):
    """
    Regression tests verifying Django CSRF token enforcement with SessionAuthentication,
    token rotation on login, rejection of stale tokens, and acceptance of fresh/rotated tokens.
    """

    def setUp(self):
        self.password = "ValidDevPass123!"
        self.user = User.objects.create_user(
            username="csrf_reg_user",
            email="csrf_reg@example.com",
            password=self.password,
            role=User.Role.DEVELOPER,
        )

    def test_login_followed_by_application_creation_with_rotated_csrf(self):
        """
        Full authentication lifecycle:
        1. Fetch pre-login CSRF token.
        2. Authenticate via POST /api/auth/login/.
        3. Verify login returns fresh rotated CSRF token in payload.
        4. Create application using the fresh rotated CSRF token -> 201 Created.
        """
        client = APIClient(enforce_csrf_checks=True)

        # Step 1: Pre-login CSRF fetch
        csrf_res = client.get("/api/auth/csrf/")
        self.assertEqual(csrf_res.status_code, status.HTTP_200_OK)
        pre_login_token = csrf_res.json()["csrfToken"]

        # Step 2: Login with pre-login CSRF token
        login_res = client.post(
            "/api/auth/login/",
            {"username": "csrf_reg_user", "password": self.password},
            HTTP_X_CSRFTOKEN=pre_login_token,
            format="json",
        )
        self.assertEqual(login_res.status_code, status.HTTP_200_OK)
        post_login_token = login_res.json().get("csrfToken")
        self.assertIsNotNone(post_login_token)
        self.assertNotEqual(pre_login_token, post_login_token)

        # Step 3: Create application using the post-login rotated token
        payload = {
            "name": "Spices E-Commerce Shop",
            "description": "Premium organic spices",
            "github_repo_url": "https://github.com/clouddeploy-demo/spices-shop",
            "default_branch": "main",
        }
        app_res = client.post(
            "/api/applications/",
            payload,
            HTTP_X_CSRFTOKEN=post_login_token,
            format="json",
        )
        self.assertEqual(app_res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(app_res.json()["name"], "Spices E-Commerce Shop")

    def test_stale_csrf_token_rejected_after_login(self):
        """
        Verify that attempting to create an application using a stale pre-login CSRF token
        is rejected by Django CSRF validation with 403 Forbidden.
        """
        client = APIClient(enforce_csrf_checks=True)

        csrf_res = client.get("/api/auth/csrf/")
        stale_token = csrf_res.json()["csrfToken"]

        login_res = client.post(
            "/api/auth/login/",
            {"username": "csrf_reg_user", "password": self.password},
            HTTP_X_CSRFTOKEN=stale_token,
            format="json",
        )
        self.assertEqual(login_res.status_code, status.HTTP_200_OK)

        # Attempt to create application using the old stale token
        payload = {
            "name": "Stale Token App",
            "github_repo_url": "https://github.com/clouddeploy-demo/stale-app",
        }
        bad_res = client.post(
            "/api/applications/",
            payload,
            HTTP_X_CSRFTOKEN=stale_token,
            format="json",
        )
        self.assertEqual(bad_res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("CSRF Failed", bad_res.json().get("detail", ""))

    def test_authenticated_csrf_endpoint_refresh_provides_valid_token(self):
        """
        Verify that GET /api/auth/csrf/ called after login provides a valid token
        for subsequent state-changing requests.
        """
        client = APIClient(enforce_csrf_checks=True)

        initial_token = client.get("/api/auth/csrf/").json()["csrfToken"]
        client.post(
            "/api/auth/login/",
            {"username": "csrf_reg_user", "password": self.password},
            HTTP_X_CSRFTOKEN=initial_token,
            format="json",
        )

        # Fetch fresh token post-login
        refreshed_token = client.get("/api/auth/csrf/").json()["csrfToken"]

        # Post application using the refreshed token
        payload = {
            "name": "Refreshed Token App",
            "github_repo_url": "https://github.com/clouddeploy-demo/refreshed-app",
        }
        app_res = client.post(
            "/api/applications/",
            payload,
            HTTP_X_CSRFTOKEN=refreshed_token,
            format="json",
        )
        self.assertEqual(app_res.status_code, status.HTTP_201_CREATED)

    def test_patch_and_deactivate_csrf_enforcement(self):
        """
        Verify that PATCH and POST /deactivate/ enforce CSRF validation.
        """
        client = APIClient(enforce_csrf_checks=True)

        init_csrf = client.get("/api/auth/csrf/").json()["csrfToken"]
        login_res = client.post(
            "/api/auth/login/",
            {"username": "csrf_reg_user", "password": self.password},
            HTTP_X_CSRFTOKEN=init_csrf,
            format="json",
        )
        valid_csrf = login_res.json()["csrfToken"]

        # Create application
        create_res = client.post(
            "/api/applications/",
            {"name": "Patch App", "github_repo_url": "https://github.com/a/b"},
            HTTP_X_CSRFTOKEN=valid_csrf,
            format="json",
        )
        app_id = create_res.json()["id"]

        # PATCH with invalid CSRF should fail
        patch_bad = client.patch(
            f"/api/applications/{app_id}/",
            {"description": "Updated"},
            HTTP_X_CSRFTOKEN="invalid-csrf-token",
            format="json",
        )
        self.assertEqual(patch_bad.status_code, status.HTTP_403_FORBIDDEN)

        # PATCH with valid CSRF should succeed
        patch_good = client.patch(
            f"/api/applications/{app_id}/",
            {"description": "Updated successfully"},
            HTTP_X_CSRFTOKEN=valid_csrf,
            format="json",
        )
        self.assertEqual(patch_good.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_good.json()["description"], "Updated successfully")

        # Deactivate with invalid CSRF should fail
        deact_bad = client.post(
            f"/api/applications/{app_id}/deactivate/",
            HTTP_X_CSRFTOKEN="invalid-csrf-token",
            format="json",
        )
        self.assertEqual(deact_bad.status_code, status.HTTP_403_FORBIDDEN)

        # Deactivate with valid CSRF should succeed
        deact_good = client.post(
            f"/api/applications/{app_id}/deactivate/",
            HTTP_X_CSRFTOKEN=valid_csrf,
            format="json",
        )
        self.assertEqual(deact_good.status_code, status.HTTP_200_OK)
        self.assertFalse(deact_good.json()["application"]["is_active"])
