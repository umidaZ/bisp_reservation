from pprint import pprint

from django.db.models import Avg, Value
from django.db.models.aggregates import Count
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.mixins import CreateModelMixin, UpdateModelMixin, RetrieveModelMixin
from rest_framework.response import Response
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
    permission_classes = [CanViewRestaurant, CanViewContent]

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

    def delete(self, request, pk):
        restaurant = get_object_or_404(self.get_queryset(), pk=pk)
        if restaurant.orderitems.count() > 0:
            return Response({'error': 'Restaurant cannot be deleted because it is associated with a reservation.'},
                            status=status.HTTP_405_METHOD_NOT_ALLOWED)
        restaurant.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        serializer.save()


class CuisineViewList(ModelViewSet):
    queryset = Cuisine.objects.annotate(restaurants_count=Count('restaurants')).all()
    serializer_class = CuisineSerializer
    permission_classes = [IsRestaurantAdminOrReadOnly]

    def delete(self, request, pk):
        cuisine = get_object_or_404(self.get_queryset(), pk=pk)
        if cuisine.restaurants.count() > 0:
            return Response({'error': 'Cuisine cannot be deleted because it includes one or more restaurants.'},
                            status=status.HTTP_405_METHOD_NOT_ALLOWED)
        cuisine.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReviewViewSet(ReadOnlyModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [CanPostReview]

    def get_queryset(self):
        return Review.objects.filter(restaurant_id=self.kwargs['restaurant_pk'])

    def get_serializer_context(self):
        return {'restaurant_id': self.kwargs['restaurant_pk']}

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
    permission_classes = [RestaurantPermissions, CanViewContent]

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
    permission_classes = [RestaurantPermissions, CanViewContent]

    def get_queryset(self):
        restaurant_id = self.kwargs.get('restaurant_id')
        return Table.objects.filter(restaurant_id=restaurant_id)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        table = self.perform_create(serializer)

        # Extract time slots from request data and add them to the table
        time_slots_data = request.data.get('time_slots', [])
        table.time_slots = time_slots_data
        table.save()

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ReservationViewSet(ModelViewSet):
    serializer_class = ReservationSerializer
    queryset = Reservation.objects.all()
    permission_classes = [CanManageReservations]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pprint(request.data)
        # Check for reservation conflicts
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

        # Check for any existing reservations for the same table and time range
        conflicts = Reservation.objects.filter(
            table=table,
            date=date,
            start_time__lte=end_time,
            end_time__gte=start_time
        ).exists()

        return not conflicts


class MenuCategoryViewSet(ModelViewSet):
    queryset = MenuCategory.objects.all()
    serializer_class = MenuCategorySerializer
    permission_classes = [RestaurantPermissions, CanViewContent]


class MenuItemViewSet(ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemsSerializer
    permission_classes = [RestaurantPermissions, CanViewContent]


class CustomerViewSet(CreateModelMixin, UpdateModelMixin, RetrieveModelMixin, GenericViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)



class PaymentStatusViewSet(ModelViewSet):
    queryset = PaymentStatus.objects.all()
    serializer_class = PaymentStatusSerializer
