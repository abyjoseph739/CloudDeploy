from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.models import User
from .models import Application
from .permissions import IsAdminOrApplicationOwner
from .serializers import ApplicationSerializer


class ApplicationListCreateView(ListCreateAPIView):
    """
    List applications accessible to the user, or register a new application.
    - Admins see all registered applications.
    - Developers see applications they created.
    - Creating an application automatically binds created_by to request.user.
    """

    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.ADMIN or user.is_superuser:
            queryset = Application.objects.all()
        else:
            queryset = Application.objects.filter(created_by=user)

        search = self.request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(name__icontains=search) | queryset.filter(description__icontains=search)

        status_filter = self.request.query_params.get("status", "").strip().lower()
        if status_filter == "active":
            queryset = queryset.filter(is_active=True)
        elif status_filter == "inactive":
            queryset = queryset.filter(is_active=False)

        return queryset.select_related("created_by")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, is_active=True)


class ApplicationDetailView(RetrieveUpdateAPIView):
    """
    Retrieve or partially update an application.
    Protected fields (id, created_by, is_active, created_at, updated_at) are read-only.
    """

    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated, IsAdminOrApplicationOwner]
    http_method_names = ["get", "patch", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.ADMIN or user.is_superuser:
            return Application.objects.all().select_related("created_by")
        return Application.objects.filter(created_by=user).select_related("created_by")


class ApplicationDeactivateView(APIView):
    """
    Soft-deactivate an application by setting is_active=False.
    Does not delete application or historical deployment records.
    """

    permission_classes = [IsAuthenticated, IsAdminOrApplicationOwner]

    def post(self, request, pk, *args, **kwargs):
        user = request.user
        try:
            if user.role == User.Role.ADMIN or user.is_superuser:
                application = Application.objects.get(pk=pk)
            else:
                application = Application.objects.get(pk=pk, created_by=user)
        except Application.DoesNotExist:
            return Response(
                {"error": "Application not found or you do not have permission to modify it."},
                status=status.HTTP_404_NOT_FOUND,
            )

        self.check_object_permissions(request, application)

        application.is_active = False
        application.save(update_fields=["is_active", "updated_at"])

        return Response(
            {
                "detail": f"Application '{application.name}' has been deactivated.",
                "application": ApplicationSerializer(application).data,
            },
            status=status.HTTP_200_OK,
        )


class ApplicationSummaryView(APIView):
    """
    Provides aggregated dashboard metrics based on actual API data.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        if user.role == User.Role.ADMIN or user.is_superuser:
            qs = Application.objects.all()
        else:
            qs = Application.objects.filter(created_by=user)

        total_count = qs.count()
        active_count = qs.filter(is_active=True).count()
        inactive_count = total_count - active_count

        return Response(
            {
                "total_applications": total_count,
                "active_applications": active_count,
                "inactive_applications": inactive_count,
                "deployments_feature_status": "planned_future_phase",
                "recent_deployments": [],
            },
            status=status.HTTP_200_OK,
        )
