from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class CustomUserManager(BaseUserManager):
	def create_user(self, email, password=None, **extra_fields):
		"""
		Creates and saves a User with the given email and password.
		"""
		if not email:
			raise ValueError("The Email field must be set")
		email = self.normalize_email(email)
		user = self.model(email=email, **extra_fields)
		user.is_active = True
		user.set_password(password)
		user.save(using=self._db)
		return user

	def create_superuser(self, email=None, password=None, **extra_fields):
		extra_fields.setdefault("is_staff", True)
		extra_fields.setdefault("is_superuser", True)

		if extra_fields.get("is_staff") is not True:
			raise ValueError("Superuser must have is_staff=True.")
		if extra_fields.get("is_superuser") is not True:
			raise ValueError("Superuser must have is_superuser=True.")

		return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
	""" User model. """

	username = None  # Email is primary user identifier, so username should be removed from defaults
	email = models.EmailField(unique=True)

	objects = CustomUserManager()

	USERNAME_FIELD = "email"
	REQUIRED_FIELDS = ["first_name", "last_name"]


	def __str__(self):
		return f"{self.first_name}-{self.last_name}"