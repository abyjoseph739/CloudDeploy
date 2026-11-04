from django.db import connection
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """
    Health check endpoint verifying API service availability and database connectivity.
    Does not expose sensitive credentials, filesystem paths, or internal stack traces.
    """

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        db_healthy = True
        try:
            connection.ensure_connection()
        except Exception:
            db_healthy = False

        payload = {
            "status": "ok" if db_healthy else "degraded",
            "service": "CloudDeploy API",
            "database": "ok" if db_healthy else "unavailable",
        }

        status_code = (
            status.HTTP_200_OK if db_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        )
        return Response(payload, status=status_code)
