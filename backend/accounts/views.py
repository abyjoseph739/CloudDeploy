from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token, rotate_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import LoginSerializer, UserSerializer


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CSRFTokenView(APIView):
    """
    Establish CSRF cookie and provide CSRF token in the response payload.
    Publicly accessible endpoint.
    """

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        token = get_token(request)
        return Response({"csrfToken": token, "detail": "CSRF cookie established."})


@method_decorator(ensure_csrf_cookie, name="dispatch")
class LoginView(APIView):
    """
    Authenticate a user using username and password via Django session authentication.
    Rotates the session and CSRF token upon successful login to prevent session fixation.
    Returns the fresh post-login CSRF token in the response payload and response cookie.
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response(
                {"error": "Invalid username or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {"error": "This account is inactive."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # login() rotates the session key and invokes rotate_token(request) for security
        login(request, user)

        # Retrieve the newly rotated CSRF token for the authenticated session
        fresh_csrf_token = get_token(request)

        return Response(
            {
                "detail": "Login successful.",
                "user": UserSerializer(user).data,
                "csrfToken": fresh_csrf_token,
            },
            status=status.HTTP_200_OK,
        )


@method_decorator(ensure_csrf_cookie, name="dispatch")
class LogoutView(APIView):
    """
    Log out the currently authenticated user, flush their session,
    and rotate the CSRF token.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        logout(request)
        rotate_token(request)
        fresh_csrf_token = get_token(request)
        return Response(
            {
                "detail": "Successfully logged out.",
                "csrfToken": fresh_csrf_token,
            },
            status=status.HTTP_200_OK,
        )


class CurrentUserView(APIView):
    """
    Return the authenticated user's safe profile information.
    Returns 401 Unauthorized for unauthenticated clients.
    """

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication credentials were not provided."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)
