from rest_framework_nested import routers
from django.urls import path
from . import views

router = routers.DefaultRouter()
router.register('restaurants', views.RestaurantViewSet, basename='restaurants')
router.register('cuisines', views.CuisineViewList)
router.register('reservations', views.ReservationViewSet)
router.register('payment_statuses', views.PaymentStatusViewSet)

restaurant_router = routers.NestedDefaultRouter(router, 'restaurants', lookup='restaurant')
restaurant_router.register('reviews', views.ReviewViewSet, basename='restaurant-reviews')
restaurant_router.register('menu_categories', views.MenuCategoryViewSet, basename='restaurant-manu_categories')


urlpatterns = [
    path('restaurants/<int:restaurant_id>/reviews/<int:review_id>/review_reply/', views.ReviewReplyViewSet.as_view({'get': 'list', 'post': 'create'}), name='review-reply'),
    path('restaurants/<int:restaurant_id>/tables/', views.TableViewSet.as_view({'get': 'list', 'post': 'create'}), name='restaurant-tables'),
    path('customers/<int:user_id>/', views.CustomerUpdateByUserId.as_view(), name='customer_update_by_user_id'),
]

urlpatterns += router.urls + restaurant_router.urls