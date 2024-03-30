from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.contrib import admin
from django.db import models
from django.template.defaultfilters import slugify
import json


class Cuisine(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    featured_restaurant = models.ForeignKey(
        'Restaurant', on_delete=models.SET_NULL, null=True, related_name='+', blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Restaurant(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    location = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    photos = models.ImageField(upload_to='restaurant/restaurant_photos/', blank=True, verbose_name='Restaurant image')
    contact_number = models.CharField(max_length=20)
    website = models.URLField(max_length=200, blank=True, null=True)
    instagram = models.CharField(max_length=100, blank=True, null=True)
    telegram = models.CharField(max_length=100, blank=True, null=True)
    opening_time = models.TimeField(null=True)
    closing_time = models.TimeField(null=True)
    is_halal = models.BooleanField(default=False, null=True)
    cuisines = models.ManyToManyField(Cuisine, related_name='restaurants', blank=True)
    num_reviews = models.IntegerField(default=0, null=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


    def __str__(self):
        return self.name

    def update_num_reviews(self):
        num_reviews = self.reviews.count()
        self.num_reviews = num_reviews
        self.save()

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Customer(models.Model):
    phone = models.CharField(max_length=255)
    birth_date = models.DateField(null=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}'

    @admin.display(ordering='user__first_name')
    def first_name(self):
        return self.user.first_name

    @admin.display(ordering='user__last_name')
    def last_name(self):
        return  self.user.last_name

    def email(self):
        return self.user.email

    class Meta:
        ordering = ['user__first_name', 'user__last_name']


class Address(models.Model):
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.street}, {self.city}'


class Table(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    number = models.IntegerField()
    capacity = models.IntegerField()
    time_slots = models.JSONField(default=list, null=True, blank=True)

    def __str__(self):
        return f'{self.restaurant}. {self.capacity} seats in table {self.number}'

    class Meta:
        unique_together = ('restaurant', 'number',)


class Reservation(models.Model):
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'
    WAITING = 'waiting'
    STATUS_CHOICES = [
        (ACCEPTED, 'Accepted'),
        (REJECTED, 'Rejected'),
        (WAITING, 'Waiting'),

    ]

    restaurant = models.ForeignKey(Restaurant, on_delete=models.PROTECT, related_name='reservations')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    num_guests = models.PositiveIntegerField()
    special_requests = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=8, blank=True, null=True, choices=STATUS_CHOICES, default=WAITING)

    def __str__(self):
        return f'{self.customer} - {self.table} - {self.date} {self.start_time}-{self.end_time}'

    def save(self, *args, **kwargs):
        if not self.is_available_for_time_slot():
            raise ValidationError("The selected time slot is not available for this table.")
        super().save(*args, **kwargs)

        date = self.date.strftime('%d-%m-%Y')
        # Add time slot to the table's time_slots list
        table = self.table
        time_slot = {
            "start_time": self.start_time.strftime('%H:%M'),
            "end_time": self.end_time.strftime('%H:%M'),
            "date": date
        }
        if time_slot not in table.time_slots:
            table.time_slots.append(time_slot)
            table.save()

    def is_available_for_time_slot(self):
        # Check if the selected time slot is available for the table
        reservations = Reservation.objects.filter(table=self.table, date=self.date)

        # Convert reservations' start and end times to tuples of (hour, minute)
        reserved_time_slots = [
            (reservation.start_time.hour, reservation.start_time.minute,
             reservation.end_time.hour, reservation.end_time.minute)
            for reservation in reservations
        ]

        # Convert new time slot to tuple of (hour, minute)
        new_time_slot = (self.start_time.hour, self.start_time.minute,
                         self.end_time.hour, self.end_time.minute)

        # Check if the new time slot overlaps with any of the reserved time slots
        for reserved_slot in reserved_time_slots:
            if (self.start_time.hour, self.start_time.minute) < (reserved_slot[2], reserved_slot[3]) and \
                    (self.end_time.hour, self.end_time.minute) > (reserved_slot[0], reserved_slot[1]):
                return False  # Time slot overlaps with a reserved slot
        return True  # Time slot is available

    def to_json(self):
        return json.dumps({
            "id": self.id,
            "restaurant": self.restaurant.id,
            "customer": self.customer.id,
            "table": self.table.id,
            "date": str(self.date),
            "start_time": self.start_time.strftime('%H:%M'),
            "end_time": self.end_time.strftime('%H:%M'),
            "num_guests": self.num_guests,
            "special_requests": self.special_requests
        })


class MenuCategory(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='menu')
    name = models.CharField(max_length=255)
    slug = models.SlugField(blank=True)

    def __str__(self):
        return f"{self.name} Menu at {self.restaurant}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('slug', 'restaurant')


class MenuItem(models.Model):
    menu = models.ForeignKey(MenuCategory, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    unit_price = models.DecimalField(
         max_digits=6,
         decimal_places=2,
         validators=[MinValueValidator(1)])
    photo = models.ImageField(upload_to='menu_photos/', blank=True)

    def __str__(self):
        return f"{self.name} - ${self.unit_price}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Review(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='reviews')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.customer} for {self.restaurant} - Rating: {self.rating}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.restaurant.update_num_reviews()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.restaurant.update_num_reviews()


class ReviewReply(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='reply')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    review = models.ForeignKey(Review, on_delete=models.CASCADE)
    reply_text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)


class PaymentStatus(models.Model):
    PENDING = 'Pending'
    COMPLETE = 'Complete'
    FAILED = 'Failed'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (COMPLETE, 'Complete'),
        (FAILED, 'Failed'),
    ]

    reservation = models.OneToOneField('Reservation', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)

    def __str__(self):
        return f"{self.reservation.customer} - {self.reservation.restaurant} - {self.status}"


class Payment(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, null=True, blank=True)
    reservation = models.OneToOneField(Reservation, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    payment_method = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment of {self.amount} made by {self.customer.first_name} at {self.timestamp}"

