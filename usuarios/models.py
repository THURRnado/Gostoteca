from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    email = models.EmailField('e-mail', unique=True, blank=False)

    def __str__(self):
        return self.username