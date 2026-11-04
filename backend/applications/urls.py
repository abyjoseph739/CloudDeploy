from django.urls import path
from .views import (
    ApplicationDeactivateView,
    ApplicationDetailView,
    ApplicationListCreateView,
    ApplicationSummaryView,
)

urlpatterns = [
    path("", ApplicationListCreateView.as_view(), name="application-list-create"),
    path("summary/", ApplicationSummaryView.as_view(), name="application-summary"),
    path("<uuid:pk>/", ApplicationDetailView.as_view(), name="application-detail"),
    path("<uuid:pk>/deactivate/", ApplicationDeactivateView.as_view(), name="application-deactivate"),
]

