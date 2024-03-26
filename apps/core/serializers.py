from django.db.models import Q
from djoser.serializers import UserSerializer as BaseUserSerializer,  UserCreateSerializer as BaseUserCreateSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.core.models import User


class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        fields = ['id', 'username', 'password', 'email', 'first_name', 'last_name']


class UserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role']


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=255, required=True)
    password = serializers.CharField(max_length=50, required=True)


class RegistrationSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=255, required=True)
    email = serializers.EmailField(max_length=254, required=True)
    password = serializers.CharField(min_length=6, max_length=50, write_only=True, required=True)
    confirm = serializers.CharField(min_length=6, max_length=50, write_only=True, required=True)
    role = serializers.IntegerField(max_value=2, min_value=1, required=True)

    def create(self, validated_data: dict):
        password = validated_data.pop('password')
        validated_data.pop("confirm")
        if not User.objects.filter(
                Q(username=validated_data.get('username')) |
                Q(email=validated_data.get('email'))
        ).exists():
            user = User(**validated_data)
            user.set_password(password)
            user.save()
            return user
        else:
            raise ValidationError({"Error": "These username and/or email exist!"})

    def validate(self, attrs: dict):
        if attrs.get("password") != attrs.get("confirm"):
            raise ValidationError({"confirm": 'Passwords must match'})
        return attrs

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name','password', 'confirm', 'role']