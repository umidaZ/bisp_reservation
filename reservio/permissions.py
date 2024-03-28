from rest_framework.permissions import BasePermission
from apps.core.models import User

class CanViewRestaurant(BasePermission):
    """
    Permission to allow viewing restaurants to all users.
    """
    def has_permission(self, request, view):
        # Allow GET requests to the RestaurantViewSet
        return view.action == 'list'


class IsAdmin(BasePermission):
    """
    Permission to allow only administrators to perform certain actions.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.ROLE.ADMIN


class IsRestaurantAdminOrReadOnly(BasePermission):
    """
    Custom permission to allow only restaurant admins to create, update, and delete restaurants.
    """
    def has_permission(self, request, view):
        # Allow GET, HEAD or OPTIONS requests
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True

        # Check if the user is a restaurant admin
        return request.user.is_authenticated and request.user.role == User.ROLE.RESTAURANT


class CanManageReservations(BasePermission):
    """
    Custom permission to allow only customers to create, update, and delete reservations.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [User.ROLE.CUSTOMER, User.ROLE.ADMIN, User.ROLE.RESTAURANT]


class CanPostReview(BasePermission):
    """
    Custom permission to allow only customers to post reviews.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.ROLE.CUSTOMER


class CanViewContent(BasePermission):
    """
    Custom permission to allow customers to view restaurant-related content.
    """
    def has_permission(self, request, view):
        # Allow GET requests for viewing restaurant-related content
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True

        # Allow customers to create, update, and delete their own reviews
        if request.method == 'POST':
            return request.user.is_authenticated and request.user.role == User.ROLE.CUSTOMER

        # Default deny for other methods
        return False