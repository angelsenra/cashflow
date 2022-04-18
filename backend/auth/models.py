from django.contrib.auth.models import AbstractUser

from helpers.models import BaseModel


class User(BaseModel, AbstractUser):
    def __str__(self):
        return f"User {self.username}"
