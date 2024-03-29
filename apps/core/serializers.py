from django.db.models import Q
from djoser.serializers import UserSerializer as BaseUserSerializer,  UserCreateSerializer as BaseUserCreateSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.core.models import User
from apps.restaurant.models import Customer, Restaurant


class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        fields = ['id', 'username', 'password',
                  'email', 'first_name', 'last_name']


class UserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role']


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=255, required=True)
    password = serializers.CharField(max_length=50, required=True)


class RegistrationSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=255, required=True)
    first_name = serializers.CharField(max_length=255, required=True)
    last_name = serializers.CharField(max_length=255, required=True)
    email = serializers.EmailField(max_length=254, required=True)
    password = serializers.CharField(
        min_length=6, max_length=50, write_only=True, required=True)
    confirm = serializers.CharField(
        min_length=6, max_length=50, write_only=True, required=True)
    birth_date = serializers.DateField(required=False)
    phone_number = serializers.CharField(max_length=255, required=False)

    def create(self, validated_data: dict):
        password = validated_data.pop('password')
        validated_data.pop("confirm")
        birth_date = validated_data.pop('birth_date', None)
        phone_number = validated_data.pop('phone_number', None)

        if not User.objects.filter(
                Q(username=validated_data.get('username')) |
                Q(email=validated_data.get('email'))
        ).exists():
            user = User.objects.create_user(
                username=validated_data['username'],
                email=validated_data['email'],
                first_name=validated_data['first_name'],
                last_name=validated_data['last_name'],
                password=password,
                role=User.ROLE.CUSTOMER)

            customer_data = {'user': user}
            if birth_date:
                customer_data['birth_date'] = birth_date
            if phone_number:
                customer_data['phone'] = phone_number

                customer = Customer.objects.create(**customer_data)

            return validated_data
        else:
            raise ValidationError(
                {"Error": "These username and/or email exist!"})

    def validate(self, attrs: dict):
        if attrs.get("password") != attrs.get("confirm"):
            raise ValidationError({"confirm": 'Passwords must match'})
        return attrs

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'confirm',
                  'birth_date', 'phone_number', 'first_name', 'last_name']


class RegisterRestaurantSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=255, required=True)
    first_name = serializers.CharField(max_length=255, required=True)
    last_name = serializers.CharField(max_length=255, required=True)
    email = serializers.EmailField(max_length=254, required=True)
    password = serializers.CharField(
        min_length=6, max_length=50, write_only=True, required=True)
    confirm = serializers.CharField(
        min_length=6, max_length=50, write_only=True, required=True)
    name = serializers.CharField(max_length=255)
    location = serializers.CharField(max_length=255)
    contact_number = serializers.CharField(max_length=20)
    website = serializers.URLField(max_length=200, required=False)
    instagram = serializers.CharField(max_length=100, required=False)
    telegram = serializers.CharField(max_length=100, required=False)
    opening_time = serializers.TimeField(required=False)
    closing_time = serializers.TimeField(required=False)
    is_halal = serializers.BooleanField(default=False)
    photos = serializers.ImageField(allow_empty_file=True, required=False)
    cuisines = serializers.ListField(
        child=serializers.IntegerField(), required=False)

    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data.pop('confirm')
        cuisines = validated_data.pop('cuisines', [])

        if not User.objects.filter(username=validated_data['username']).exists():
            user = User.objects.create_user(
                username=validated_data['username'],
                email=validated_data['email'],
                first_name=validated_data['first_name'],
                last_name=validated_data['last_name'],
                password=password,
                role=User.ROLE.RESTAURANT)

            restaurant_data = {
                'name': validated_data['name'],
                'location': validated_data['location'],
                'contact_number': validated_data['contact_number'],
                'website': validated_data.get('website'),
                'instagram': validated_data.get('instagram'),
                'telegram': validated_data.get('telegram'),
                'opening_time': validated_data.get('opening_time'),
                'closing_time': validated_data.get('closing_time'),
                'is_halal': validated_data.get('is_halal'),
                'photos': validated_data.get('photos'),
                'user': user,
            }
            restaurant = Restaurant.objects.create(**restaurant_data)

            if cuisines:
                restaurant.cuisines.add(*cuisines)
            return restaurant
        else:
            raise ValidationError({'error': 'Username already exists'})

    def to_representation(self, instance):
        representation = instance.__dict__
        del representation['_state']
        del representation['photos']
        return representation

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm']:
            raise ValidationError({'confirm': 'Passwords must match'})
        return attrs

    class Meta:
        fields = ['id', 'username', 'email', 'password', 'confirm', 'name', 'location', 'contact_number',
                  'website', 'instagram', 'telegram', 'opening_time', 'closing_time', 'is_halal', 'cuisines', 'first_name', 'last_name']
