from django.contrib.auth.models import AbstractUser

from helpers.models import BaseModel


class User(BaseModel, AbstractUser):
    pass
