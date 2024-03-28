from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models


class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given phone and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields["role"] = User.ROLE.ADMIN

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    class ROLE(models.IntegerChoices):
        ADMIN = (0, "admin")
        RESTAURANT = (1, "restaurant")
        CUSTOMER = (2, "customer")

    email = models.EmailField(unique=True)

    role = models.SmallIntegerField(
        choices=ROLE.choices,
        default=ROLE.CUSTOMER
    )

    def __str__(self):
        return self.fio

    @property
    def fio(self):
        return f"{self.first_name} {self.last_name}".rstrip(" ")