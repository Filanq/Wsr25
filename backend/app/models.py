import base64
import binascii
import random
import tempfile
from django.core.files.base import ContentFile
from django.db import models
from django.contrib.auth.models import AbstractBaseUser
import os
from django.core.validators import MinValueValidator


class Service(models.Model):
    name = models.CharField(max_length=250)
    time = models.CharField(max_length=250)

    class Meta:
        verbose_name_plural = 'Услуги'
        verbose_name = 'услуга'

    def __str__(self):
        return self.name


class User(AbstractBaseUser):
    login = models.CharField(max_length=250)
    password = models.CharField(max_length=250)
    services = models.CharField(max_length=500)

    class Meta:
        verbose_name_plural = 'Операторы'
        verbose_name = 'оператор'

    def __str__(self):
        return self.login


class Records(AbstractBaseUser):
    place = models.CharField(max_length=250)
    services = models.CharField(max_length=250)
    datetime = models.DateTimeField()
    status = models.CharField(max_length=250)
    link = models.CharField(max_length=250)

    class Meta:
        verbose_name_plural = 'Операторы'
        verbose_name = 'оператор'

    def __str__(self):
        return self.login


class Token(models.Model):
    key = models.CharField(max_length=40, primary_key=True)
    user = models.OneToOneField(
        User, related_name='auth_token',
        on_delete=models.CASCADE
    )
    created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super().save(*args, **kwargs)

    @classmethod
    def generate_key(cls):
        return binascii.hexlify(os.urandom(20)).decode()

    def __str__(self):
        return self.key
