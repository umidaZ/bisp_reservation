from django.contrib.auth import authenticate, login
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework import status

from apps.core.models import User
from apps.core.serializers import LoginSerializer, UserSerializer, RegistrationSerializer
from apps.restaurant.models import Customer, Restaurant


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data.get('username')
        password = serializer.validated_data.get('password')
        user = authenticate(username=username, password=password)
        if user is None:
            raise ValidationError({'password': 'Username and/or password is incorrect'})
        login(request, user)
        serializer = UserSerializer(user)
        refresh = RefreshToken.for_user(user=user)
        data = {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": serializer.data
        }
        return Response(data)


class RegistrationView(generics.CreateAPIView):
    permission_classes = [~IsAuthenticated]
    serializer_class = RegistrationSerializer


def perform_create(self, serializer):
    user = serializer.save()
    refresh = RefreshToken.for_user(user)
    user_data = UserSerializer(user).data
    data = {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": user_data
    }

    if user.role == User.ROLE.CUSTOMER:
        Customer.objects.create(user=user)
    elif user.role == User.ROLE.RESTAURANT:
        Restaurant.objects.create(user=user)

    return Response(data, status=status.HTTP_201_CREATED)
class UserMeView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
    

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
                return Response({"message": "Logout successful."}, status=status.HTTP_205_RESET_CONTENT)
            else:
                return Response({"error": "Refresh token not provided."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Failed to logout.", "details": str(e)}, status=status.HTTP_400_BAD_REQUEST)