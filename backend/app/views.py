import json
import os
import re

from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.password_validation import validate_password
from django.shortcuts import render, HttpResponse, HttpResponseRedirect, redirect
from rest_framework import viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from .serializers import UserSerializer, ServiceSerializer
from .models import User, Token, Service
from django.http import Http404
from rest_framework import status
from django.core.exceptions import RequestDataTooBig, ValidationError


def get_user(request, throw_exception=True):
    if request.META.get('HTTP_AUTHORIZATION'):
        token = request.META.get('HTTP_AUTHORIZATION').split('Token ')[1]
    else:
        if throw_exception:
            return Response({"detail": "Учетные данные не были предоставлены."}, 401)
        else:
            return None
    if not token:
        if throw_exception:
            return Response({"detail": "Учетные данные не были предоставлены."}, 401)
        else:
            return None
    elif not Token.objects.filter(key=token).exists():
        if throw_exception:
            return Response({"detail": "Учетные данные не были предоставлены."}, 401)
        return None
    token = Token.objects.get(key=token)
    return token.user


class UsersList(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.data)
        try:
            validate_password(data['password'], data['username'])
        except ValidationError as e:
            return Response({"password": e}, status=400)

        data['password'] = make_password(data['password'])
        user = User(**data)
        user.save()
        data['id'] = user.pk
        return Response(data, status=status.HTTP_201_CREATED)


class ServicesList(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer


@api_view(['POST'])
def login(request):
    data = request.data
    try:
        email = data['login']
    except KeyError:
        return Response({"login": ["Введите логин."]}, 401)
    try:
        password = data['password']
    except KeyError:
        return Response({"password": ["Введите пароль."]}, 401)

    if User.objects.filter(login=login).exists():
        user = User.objects.get(login=login)
        if password == user.password:
            if Token.objects.filter(user=user).exists():
                Token.objects.get(user=user).delete()
            token = Token.objects.create(user=user)
            return Response({"token": token.key}, 200)
    return Response({"login": ["Неверные данные"]}, 400)


@api_view(['POST'])
def logout(request):
    token = request.META.get('HTTP_AUTHORIZATION').split('Token ')[1]
    if not token:
        return Response({"detail": "Пользователь не авторизован."}, 401)
    elif not Token.objects.filter(key=token).exists():
        return Response({"detail": "Учетные данные не были предоставлены."}, 401)
    token = Token.objects.get(key=token).delete()
    return Response({}, 204)
