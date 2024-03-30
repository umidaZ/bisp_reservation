from django.contrib.auth import authenticate, login
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework.views import APIView
from rest_framework import status

from apps.core.models import User
from apps.core.serializers import LoginSerializer, RegisterRestaurantSerializer, UserSerializer, RegistrationSerializer
from apps.restaurant.models import Customer, Restaurant


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request, username=serializer.validated_data['username'], password=serializer.validated_data['password'])

        if user:
            login(request, user)
            token = RefreshToken.for_user(user)
            data = {"token": str(token), "user": UserSerializer(user).data}
            return Response(data, status=status.HTTP_200_OK)
        else:
            raise ValidationError(
                {'error': 'Invalid username or password'})



class RegistrationView(generics.CreateAPIView):
    permission_classes = [~IsAuthenticated]
    serializer_class = RegistrationSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        user = User.objects.get(id=serializer.data['user_id'])
        token = RefreshToken.for_user(user)
        data = {"token": str(token), "data": serializer.data}

        return Response(data, status=status.HTTP_201_CREATED)


class RestaurantRegistrationView(generics.CreateAPIView):
    permission_classes = [~IsAuthenticated]
    serializer_class = RegisterRestaurantSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        user = User.objects.get(id=serializer.data['user_id'])
        token = RefreshToken.for_user(user)
        data = {"token": str(token), "data": serializer.data}

        return Response(data, status=status.HTTP_201_CREATED)


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
