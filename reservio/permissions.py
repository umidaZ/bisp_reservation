from rest_framework.permissions import BasePermission

from apps.core.models import User


class CanViewRestaurant(BasePermission):
    """
    Permission to allow viewing restaurants to all users.
    """

    def has_permission(self, request, view):
        # Allow GET requests to the RestaurantViewSet
        return view.action == 'list'


class RestrictPostRequest(BasePermission):
    def has_permission(self, request, view):
        return request.method != "POST"


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == User.ROLE.ADMIN


class IsUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == User.ROLE.USER


from rest_framework import permissions

class IsRestaurantAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow only restaurant admins to create, update, and delete restaurants.
    """

    def has_permission(self, request, view):
        # Allow GET, HEAD or OPTIONS requests
        if request.method in permissions.SAFE_METHODS:
            return True

        # Check if the user is a restaurant admin
        return request.user.is_authenticated and request.user.role == User.ROLE.RESTAURANT


class RestaurantPermissions(permissions.BasePermission):
    """
    Custom permission to allow only restaurant admins to create, update, and delete cuisines.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.ROLE.RESTAURANT



class CanManageReservations(permissions.BasePermission):
    """
    Custom permission to allow only customers to create, update, and delete reservations.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [User.ROLE.CUSTOMER, User.ROLE.ADMIN, User.ROLE.RESTAURANT]


class CanPostReview(permissions.BasePermission):
    """
    Custom permission to allow only customers to post reviews.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.ROLE.CUSTOMER


class CanViewContent(permissions.BasePermission):
    """
    Custom permission to allow customers to view restaurant-related content.
    """

    def has_permission(self, request, view):
        # Allow GET requests for viewing restaurant-related content
        if request.method in permissions.SAFE_METHODS:
            return True

        # Allow customers to create, update, and delete their own reviews
        if request.method == 'POST':
            return request.user.is_authenticated and request.user.role == User.ROLE.CUSTOMER

        # Default deny for other methods
        return False