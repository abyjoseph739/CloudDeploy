from unittest.mock import patch
from django.db import DatabaseError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient


class HealthCheckEndpointTests(TestCase):
    """Tests for the GET /api/health/ endpoint in the common app."""

    def setUp(self):
        self.client = APIClient()

    def test_health_check_healthy(self):
        """GET /api/health/ returns HTTP 200 and expected status when DB is healthy."""
        response = self.client.get("/api/health/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("service"), "CloudDeploy API")
        self.assertEqual(data.get("database"), "ok")

    def test_health_check_database_failure(self):
        """GET /api/health/ returns HTTP 503 degraded without leaking internal details when DB fails."""
        with patch("django.db.connection.ensure_connection", side_effect=DatabaseError("Connection timeout")):
            response = self.client.get("/api/health/")

            self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
            data = response.json()
            self.assertEqual(data.get("status"), "degraded")
            self.assertEqual(data.get("service"), "CloudDeploy API")
            self.assertEqual(data.get("database"), "unavailable")
            # Verify no exception messages, passwords, or stack traces are leaked
            self.assertNotIn("Connection timeout", str(response.content))
            self.assertNotIn("Traceback", str(response.content))

    def test_health_check_unauthenticated_access(self):
        """Health check endpoint should be accessible without authentication."""
        self.client.logout()
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
