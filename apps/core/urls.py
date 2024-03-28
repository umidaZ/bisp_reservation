from django.urls import path, include

from apps.core.views import LoginView, RegistrationView, RestaurantRegistrationView, UserMeView, LogoutView

app_name = "auth"

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('registration/', RegistrationView.as_view(), name='registration'),
    path('restaurant/registration/', RestaurantRegistrationView.as_view(), name='restaurant-registration'),
    path('user/me/', UserMeView.as_view(), name='user-me'),
    path('logout/', LogoutView.as_view(), name='logout')
]
