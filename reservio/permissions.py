from rest_framework.permissions import BasePermission

from apps.core.models import User


class CanViewRestaurant(BasePermission):
    """
    Permission to allow viewing restaurants to all users.
    """

    def has_permission(self, request, view):
        # Allow GET requests to the RestaurantViewSet
        return view.action == 'list'


class CanReserveRestaurant(BasePermission):
    """
    Permission to allow reservation of restaurants only for authenticated users.
    """

    def has_permission(self, request, view):
        # Allow POST requests to the ReservationViewSet only for authenticated users
        return request.method != 'POST'


class CanPostReview(BasePermission):
    """
    Permission to allow posting reviews only for authenticated users.
    """

    def has_permission(self, request, view):
        # Allow POST requests to the ReviewViewSet only for authenticated users
        return request.method != 'POST'


class RestrictPostRequest(BasePermission):
    def has_permission(self, request, view):
        return request.method != "POST"


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == User.ROLE.ADMIN


class IsUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == User.ROLE.USER
