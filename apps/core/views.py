from django.contrib.auth import authenticate, login
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.serializers import LoginSerializer, UserSerializer, RegistrationSerializer


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


class UserMeView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user