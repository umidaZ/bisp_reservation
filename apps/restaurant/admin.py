from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from apps.tags.models import TaggedItem
from . import models
from django.db.models import Count
from django.utils.html import format_html, urlencode
from django.urls import reverse


class TagInline(GenericTabularInline):
    autocomplete_fields = ['tag']
    model = TaggedItem


@admin.register(models.Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    inlines = [TagInline]
    autocomplete_fields = ['cuisines']
    prepopulated_fields = {
        'slug': ['name']
    }
    list_display = (
    'name', 'location', 'is_halal', 'number_of_reservations', 'number_of_reviews')
    list_filter = ('is_halal', 'cuisines')
    search_fields = ('name__istartswith', 'location_istartswith')
    list_per_page = 10

    @admin.display(ordering='number_of_reservations')
    def number_of_reservations(self, restaurant):
        url = (
                reverse('admin:restaurant_reservation_changelist')
                + '?'
                + urlencode({
            'restaurant__id': str(restaurant.id)
        }))
        return format_html('<a href="{}">{} Reservations</a>', url, restaurant.number_of_reservations)

    @admin.display(ordering='number_of_reviews')
    def number_of_reviews(self, restaurant):
        url = (
                reverse('admin:restaurant_review_changelist')
                + '?'
                + urlencode({'restaurant__id': str(restaurant.id)})
        )
        return format_html('<a href="{}">{}</a>', url, restaurant.number_of_reviews)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            number_of_reservations=Count('reservations'),
            number_of_reviews=Count('reviews')
        )


@admin.register(models.Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('email', 'phone', 'birth_date', 'reserved_restaurants')
    search_fields = ('first_name__istartswith', 'last_name__istartswith')
    list_select_related = ['user']
    autocomplete_fields = ['user']
    list_editable = ('phone', 'birth_date')
    list_per_page = 10

    @admin.display(ordering='reserved_restaurants')
    def reserved_restaurants(self, customer):
        url = (
                reverse('admin:restaurant_reservation_changelist')
                + '?'
                + urlencode({
            'customer__id': str(customer.id)
        }))
        return format_html('<a href="{}">{} Reservations</a>', url, customer.reserved_restaurants)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            reserved_restaurants=Count('reservation')
        )



@admin.register(models.Reservation)
class ReservationAdmin(admin.ModelAdmin):
    dynamic_raw_id_fields = ('table',)
    list_display = ('customer', 'restaurant', 'date', 'num_guests')
    list_filter = ('restaurant',)
    search_fields = ('customer__first_name__istartswith', 'customer__last_name__istartswith', 'restaurant__name__istartswith')
    list_editable = ('date', 'num_guests',)
    list_per_page = 10

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "table":
            selected_restaurant_id = request.POST.get('restaurant') or request.GET.get('restaurant')
            print("Selected Restaurant ID:", selected_restaurant_id)  # Debug output
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(models.Cuisine)
class CuisineAdmin(admin.ModelAdmin):
    prepopulated_fields = {
        'slug': ['name']
    }
    list_display = ['name', 'restaurants_count']
    search_fields = ['name__istartswith']

    @admin.display(ordering='restaurants_count')
    def restaurants_count(self, cuisines):
        url = (
            reverse('admin:restaurant_restaurant_changelist')
            + '?'
            + urlencode({
                'cuisines__id': str(cuisines.id)
            }))
        return format_html('<a href="{}">{} Restaurants</a>', url, cuisines.restaurants_count)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            restaurants_count=Count('restaurants')
        )


@admin.register(models.Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ['restaurant', 'number', 'capacity']
    list_filter = ['restaurant',]


@admin.register(models.MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {
        'slug': ['name']
    }


@admin.register(models.MenuItem)
class MenuCategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {
        'slug': ['name']
    }


admin.site.register(models.PaymentStatus)
admin.site.register(models.Review)
admin.site.register(models.ReviewReply)
admin.site.register(models.Payment)







