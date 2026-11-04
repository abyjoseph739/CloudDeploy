from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

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
        # Verify raw password is not stored in plaintext
        self.assertNotEqual(user.password, raw_password)
        self.assertTrue(user.check_password(raw_password))
        self.assertFalse(user.check_password("WrongPassword!"))

        # Verify authentication backend works as expected
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
