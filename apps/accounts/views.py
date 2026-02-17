from django.contrib.auth import login
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import (
    ChangePasswordSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
    UserUpdateSerializer,
)


class RegisterView(generics.CreateAPIView):
    """
    API endpoint for new user registration:

    Notice: AllowAny: Accessible by unauthenticated users.

    Flow:
    1) Client sends POST request.
    2) DRF looks for method create (overridden in this case):
        a) self.get_serializer(data=) is best-practise to initialize the serializer.
        b) .is_valid() calls all validation methods inside serializer.
        c) raise_exception=True if any validation fails -> will show error to client.
        d) .save() calls create method in serializer. (creates user in db with hashed password)
        e) SimpleJWT creates refresh and access token for this user.
        f) response contains 201 status code and user's data processed through ProfileSerializer -> so data are safe.
    """

    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh_token = RefreshToken.for_user(user)
        access_token = refresh_token.access_token

        return Response(
            {
                "user": UserProfileSerializer(user).data,
                "refresh": str(refresh_token),
                "access": str(access_token),
                "message": "User registered successfully",
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(generics.GenericAPIView):
    """
    API endpoint for user authentication:

    Notice: GenericAPIView requires manual implementation of the POST method.

    Flow:
    1) Client sends POST request with credentials.
    2) inside post():
        a) self.get_serializer(data=request.data) initializes the validation process.
        b) .is_valid() calls all validation methods inside serializer.
        c) raise_exception=True if any validation fails -> will show error to client.
        d) User object is retrieved from serializer.validated_data (set during validation).
        e) logining user. (to create a standard Django session in the DB)
        f) SimpleJWT creates refresh and access token for this user.
        g) Response returns 200 OK with safe user data (via ProfileSerializer) and tokens.
    """

    serializer_class = UserLoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        login(request, user)

        refresh_token = RefreshToken.for_user(user)
        access_token = refresh_token.access_token

        return Response(
            {
                "user": UserProfileSerializer(user).data,
                "refresh": str(refresh_token),
                "access": str(access_token),
                "message": "User login successfully",
            },
            status=status.HTTP_200_OK,
        )


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for retrieving and updating user's profile:

    Notice: No PK in URL: We use the request.user to identify the object.

    Flow:
    1) get_object(): Overridden to return self.request.user.
    2) get_serializer_class() sets different serializers for request methods.
    3) GET: DRF takes the object from get_object, passes it to the serializer, and returns 200 OK.
    4) Update (PUT/PATCH): DRF handles validation, calls .save() on the serializer, and updates the user in the DB.
    """

    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        match self.request.method:
            case "PUT" | "PATCH":
                return UserUpdateSerializer
            case _:
                return super().get_serializer_class()


class ChangePasswordView(generics.UpdateAPIView):
    """
    API endpoint for password update:

    Flow:
    1) get_object(): Returns current authenticated user (self.request.user).
    2) update() method is overridden. Sets new password after validations and response contains message.
    """

    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"message": "password changed successfully"}, status=status.HTTP_200_OK
        )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """
    API endpoint to logout:

    Flow:
    1) Getting "refresh_token" from request.data.
    2) if ok -> putting token in blacklist and response 200 with message.
    3) if not -> 400 code with error message.
    """

    try:
        refresh_token = request.data.get("refresh_token")
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
    except TokenError:
        return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)
