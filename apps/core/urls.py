from django.urls import path, include

from apps.core.views import LoginView, RegistrationView, UserMeView

app_name = "auth"

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('registration/', RegistrationView.as_view(), name='registration'),
    path('user/me/', UserMeView.as_view(), name='user-me')
]
