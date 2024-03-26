from datetime import datetime
from rest_framework import serializers
from .models import Restaurant, Cuisine, Review, ReviewReply, Table, Reservation, Customer, Payment, PaymentStatus, MenuCategory, MenuItem


class CuisineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cuisine
        fields = ['id', 'name', 'restaurants_count']

    restaurants_count = serializers.IntegerField(read_only=True)


class RestaurantSerializer(serializers.ModelSerializer):
    cuisines = CuisineSerializer(many=True)
    rating = serializers.SerializerMethodField()
    num_reviews = serializers.SerializerMethodField()

    class Meta:
        model = Restaurant
        fields = \
            ['id', 'name', 'slug', 'location', 'description', 'photos', 'contact_number', 'website',
             'instagram', 'telegram', 'opening_time', 'closing_time', 'rating', 'num_reviews', 'is_halal', 'cuisines']

    def get_rating(self, obj):
        # Retrieve all reviews associated with this restaurant
        reviews = obj.reviews.all()

        # Calculate the average rating from the reviews
        if reviews.exists():
            total_rating = sum(review.rating for review in reviews)
            return total_rating / len(reviews)
        else:
            return 0  # If there are no reviews, return 0 as the default rating

    def get_num_reviews(self, obj):  # Add this method
        return obj.reviews.count()


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'restaurant', 'customer', 'rating', 'comment', 'timestamp']

    def create(self, validated_data):
        restaurant_id = self.context['restaurant_id']
        return Review.objects.create(restaurant_id=restaurant_id, **validated_data)


class ReviewReplySerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    restaurant = serializers.PrimaryKeyRelatedField(read_only=True)
    customer = serializers.PrimaryKeyRelatedField(read_only=True)
    review = serializers.PrimaryKeyRelatedField(read_only=True)
    timestamp = serializers.DateTimeField(read_only=True)

    class Meta:
        model = ReviewReply
        fields = ['id', 'restaurant', 'customer', 'review', 'reply_text', 'timestamp']

    def create(self, validated_data):
        review_id = self.context['review_id']
        restaurant_id = self.context['restaurant_id']

        customer_id = Review.objects.get(id=review_id).customer_id

        return ReviewReply.objects.create(review_id=review_id, restaurant_id=restaurant_id, customer_id=customer_id, **validated_data)


class TableSerializer(serializers.ModelSerializer):
    restaurant = serializers.PrimaryKeyRelatedField(queryset=Restaurant.objects.all())

    class Meta:
        model = Table
        fields = ['id', 'restaurant', 'number', 'capacity', 'time_slots']
        read_only_fields = ['id', 'time_slots']


class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = ['id', 'restaurant', 'customer', 'table', 'date', 'start_time', 'end_time', 'num_guests', 'special_requests']

    def create(self, validated_data):
        reservation = Reservation.objects.create(**validated_data)
        return reservation

    def update(self, instance, validated_data):
        instance.start_time = validated_data.get('start_time', instance.start_time)
        instance.end_time = validated_data.get('end_time', instance.end_time)

        instance.restaurant = validated_data.get('restaurant', instance.restaurant)
        instance.customer = validated_data.get('customer', instance.customer)
        instance.table = validated_data.get('table', instance.table)
        instance.date = validated_data.get('date', instance.date)
        instance.num_guests = validated_data.get('num_guests', instance.num_guests)
        instance.special_requests = validated_data.get('special_requests', instance.special_requests)
        instance.save()

        return instance

    def validate(self, data):
        table = data['table']
        date = data['date']
        start_time = data['start_time']
        end_time = data['end_time']
        num_guests = data.get('num_guests', 0)

        # Check if the table can accommodate the number of guests
        if num_guests > table.capacity:
            raise serializers.ValidationError("Number of guests exceeds table capacity.")

        # Check if the start time is before the end time
        if start_time >= end_time:
            raise serializers.ValidationError("End time must be after start time.")

        # Validate date to ensure it's not in the past
        today = date.today()
        if date < today:
            raise serializers.ValidationError("Reservation date cannot be in the past.")

        # Validate start time based on the date
        current_time = datetime.now().time()
        if date == today and start_time < current_time:
            raise serializers.ValidationError("Reservation start time cannot be in the past for today's date.")

        # You can add additional date validation logic here, such as checking if the date
        # is within a certain range or falls on a specific day of the week.

        return data


class MenuCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuCategory
        fields = ['id', 'restaurant', 'name', 'slug']


class MenuItemsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ['id', 'customer', 'restaurant', 'reservation', 'amount', 'payment_method', 'transaction_id']


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'phone', 'birth_date']


class PaymentStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentStatus
        fields = ['id', 'reservation', 'status']

