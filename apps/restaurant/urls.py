from rest_framework_nested import routers
from django.urls import path
from . import views

router = routers.DefaultRouter()
router.register('restaurants', views.RestaurantViewSet, basename='restaurants')
router.register('cuisines', views.CuisineViewList)
router.register('reservations', views.ReservationViewSet)
router.register('customers', views.CustomerViewSet)
router.register('payment_statuses', views.PaymentStatusViewSet)

restaurant_router = routers.NestedDefaultRouter(router, 'restaurants', lookup='restaurant')
restaurant_router.register('reviews', views.ReviewViewSet, basename='restaurant-reviews')
restaurant_router.register('menu_categories', views.MenuCategoryViewSet, basename='restaurant-manu_categories')

# restaurant_router.register('tables', views.TableViewSet, basename='restaurant-tables')

urlpatterns = [
    path('restaurants/<int:restaurant_id>/reviews/<int:review_id>/review_reply/', views.ReviewReplyViewSet.as_view({'get': 'list', 'post': 'create'}), name='review-reply'),
    path('restaurants/<int:restaurant_id>/tables/', views.TableViewSet.as_view({'get': 'list', 'post': 'create'}), name='restaurant-tables'),
]

urlpatterns += router.urls + restaurant_router.urls