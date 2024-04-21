from pprint import pprint

from django.db.models import Avg, Value
from django.db.models.aggregates import Count
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from apps.core.models import User
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.mixins import CreateModelMixin, UpdateModelMixin, RetrieveModelMixin
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet, GenericViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny

from reservio.permissions import CanViewRestaurant, CanPostReview, IsRestaurantAdminOrReadOnly, CanManageReservations, CanViewContent, RestaurantPermissions
from .filters import RestaurantFilter
from .models import Restaurant, Cuisine, Review, ReviewReply, Table, Reservation, Customer, PaymentStatus, \
    MenuCategory, MenuItem
from .pagination import DefaultPagination
from .serializers import RestaurantSerializer, CuisineSerializer, ReviewSerializer, ReviewReplySerializer, \
    TableSerializer, ReservationSerializer, CustomerSerializer, PaymentStatusSerializer, MenuCategorySerializer, \
    MenuItemsSerializer


class RestaurantViewSet(ModelViewSet):
    pagination_class = DefaultPagination

    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = RestaurantFilter
    search_fields = ['name', 'location', 'cuisines__name']

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset=queryset)
        return queryset.annotate(
            rating=Coalesce(Avg('reviews__rating'), Value(0.0))
        ).order_by('-rating')

    def get_serializer_context(self):
        return {'request': self.request}

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save()

    def get_queryset(self):
        return super().get_queryset()


class CuisineViewList(ModelViewSet):
    queryset = Cuisine.objects.annotate(
        restaurants_count=Count('restaurants')).all()
    serializer_class = CuisineSerializer
    permission_classes = [IsRestaurantAdminOrReadOnly]

    def delete(self, request, pk):
        cuisine = get_object_or_404(self.get_queryset(), pk=pk)
        if cuisine.restaurants.count() > 0:
            return Response({'error': 'Cuisine cannot be deleted because it includes one or more restaurants.'},
                            status=status.HTTP_405_METHOD_NOT_ALLOWED)
        cuisine.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReviewViewSet(ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [CanViewContent]

    def get_queryset(self):
        if self.request.user.role == User.ROLE.RESTAURANT:
            restaurant = self.request.user.restaurant
            return Review.objects.filter(restaurant=restaurant)
        elif 'restaurant_id' in self.kwargs:
            return Review.objects.filter(restaurant_id=self.kwargs['restaurant_id'])
        else:
            return Review.objects.none()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        instance = serializer.save()
        self.update_restaurant_rating(instance.restaurant)

    def update_restaurant_rating(self, restaurant):
        review_count = restaurant.reviews.count()
        if review_count == 0:
            restaurant.rating = 0
        else:
            average_rating = restaurant.reviews.aggregate(Avg('rating'))['rating__avg']
            restaurant.rating = average_rating
        restaurant.save()


class ReviewReplyViewSet(ModelViewSet):
    serializer_class = ReviewReplySerializer
    # permission_classes = [RestaurantPermissions]

    def get_queryset(self):
        review_id = self.kwargs['review_id']
        restaurant_id = self.kwargs['restaurant_id']

        return ReviewReply.objects.filter(review_id=review_id, restaurant_id=restaurant_id)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        return {
            'review_id': self.kwargs['review_id'],
            'restaurant_id': self.kwargs['restaurant_id'],
            **context
        }


class TableViewSet(ModelViewSet):
    serializer_class = TableSerializer
    queryset = Table.objects.all()
    permission_classes = [CanViewContent]

    def perform_create(self, serializer):
        try:
            # Example: Saving the serializer with validated data to create the object
            table = serializer.save()
            print(f"Created table object: {table}")  # Debugging statement
            return table
        except Exception as e:
            print(f"Error creating table: {e}")  # Log the error
            return None

    def get_queryset(self):
        restaurant_id = self.kwargs.get('restaurant_id')
        return Table.objects.filter(restaurant_id=restaurant_id)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            table = self.perform_create(serializer)
            if table is None:
                raise ValueError("Table creation failed - perform_create returned None")

            # Extract time slots from request data and add them to the table
            time_slots_data = request.data.get('time_slots', [])
            table.time_slots = time_slots_data
            table.save()

            serialized_table = self.get_serializer(table).data
            return Response(serialized_table, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class ReservationViewSet(ModelViewSet):
    serializer_class = ReservationSerializer
    queryset = Reservation.objects.all()
    permission_classes = [CanManageReservations]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not self.check_reservation_conflict(serializer.validated_data):
            return Response({"error": "The selected time slot is not available for this table."},
                            status=status.HTTP_400_BAD_REQUEST)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def check_reservation_conflict(self, validated_data):
        table = validated_data['table']
        date = validated_data['date']
        start_time = validated_data['start_time']
        end_time = validated_data['end_time']

        conflicts = Reservation.objects.filter(
            table=table,
            date=date,
            start_time__lte=end_time,
            end_time__gte=start_time
        ).exists()

        return not conflicts


class RestaurantReservation(APIView):

    def get(self, request, restaurant_id):
        restaurant = Restaurant.objects.get(id=restaurant_id)
        reservations = Reservation.objects.filter(restaurant=restaurant)
        serializer = ReservationSerializer(reservations, many=True)
        return Response({"status": "ok", "data": serializer.data})


class ManageReservation(APIView):

    def get(self, request, pk=None):  # Make 'pk' optional by setting default value to None
        if pk is not None:
            # Fetch a specific reservation
            try:
                reservation = Reservation.objects.get(id=pk)
                serializer = ReservationSerializer(reservation)
                return Response({"status": "ok", "data": serializer.data})
            except Reservation.DoesNotExist:
                return Response({"status": "error", "message": "Reservation not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            # List reservations for the current user
            user = request.user  # Assuming user authentication is set up correctly
            reservations = Reservation.objects.filter(customer=user.customer)
            serializer = ReservationSerializer(reservations, many=True)
            return Response({"status": "ok", "data": serializer.data})

    def post(self, request, pk=None):  # Same here, 'pk' is optional
        if pk is not None:
            # Handle POST request for updating a specific reservation
            try:
                reservation = Reservation.objects.get(id=pk)
                status_value = request.data.get('status', Reservation.WAITING)
                reservation.status = status_value
                reservation.save()
                serializer = ReservationSerializer(reservation)
                return Response({"status": "ok", "data": serializer.data})
            except Reservation.DoesNotExist:
                return Response({"status": "error", "message": "Reservation not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            # Handle POST request for creating a new reservation
            serializer = ReservationSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"status": "ok", "data": serializer.data}, status=status.HTTP_201_CREATED)
            return Response({"status": "error", "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class MenuCategoryViewSet(ModelViewSet):
    queryset = MenuCategory.objects.all()
    serializer_class = MenuCategorySerializer
    permission_classes = [RestaurantPermissions, CanViewContent]


class MenuCategoriesView(APIView):
    permission_classes = [IsRestaurantAdminOrReadOnly]

    def get(self, request, restaurant_id):
        restaurant = Restaurant.objects.get(id=restaurant_id)
        categories = MenuCategory.objects.filter(restaurant=restaurant)
        data = MenuCategorySerializer(categories, many=True).data
        return Response({"status": "ok", "data": data})

    def post(self, request, restaurant_id):
        restaurant = Restaurant.objects.get(id=restaurant_id)
        serializer = MenuCategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(restaurant=restaurant)  # Save with restaurant instance
            return Response({"status": "ok", "category": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MenuItemsView(APIView):
    def get(self, request, category_id):
        category = MenuCategory.objects.get(id=category_id)
        items = MenuItem.objects.filter(menu=category)
        data = MenuItemsSerializer(items, many=True).data
        return Response({"status": "ok", "data": data})

    def post(self, request):
        serializer = MenuItemsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
        else:
            print(serializer.errors)

        return Response({"status": "ok", "data": serializer.data})


class MenuItemViewSet(ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemsSerializer
    permission_classes = [RestaurantPermissions, CanViewContent]


class CustomerUpdateByUserId(APIView):
    def patch(self, request, user_id):
        try:
            customer = Customer.objects.get(user_id=user_id)
        except Customer.DoesNotExist:
            return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = CustomerSerializer(
            customer, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class PaymentStatusViewSet(ModelViewSet):
    queryset = PaymentStatus.objects.all()
    serializer_class = PaymentStatusSerializer
