import json
import os
import re

from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.password_validation import validate_password
from django.shortcuts import render, HttpResponse, HttpResponseRedirect, redirect
from rest_framework import viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from .serializers import UserSerializer
from .models import User, Token
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

#     def list(self, request, *args, **kwargs):
#         curr_user = get_user(request, throw_exception=False)
#         page = request.GET.get('page', 1)
#         limit = request.GET.get('limit', 3)
#         page = int(page)
#         limit = int(limit)
#         users = User.objects.all()
#         users_count = User.objects.count()
#         users = users[limit * (page - 1):limit + (limit * (page - 1))]
#
#         serializer = self.get_serializer(users, many=True)
#         users = serializer.data
#         for key in range(0, len(users)):
#             if not (curr_user is None):
#                 if Subscribe.objects.filter(user=curr_user, subscribe_id=users[key]['id']).exists():
#                     users[key]['is_subscribed'] = True
#             if "is_subscribed" not in users[key]:
#                 users[key]['is_subscribed'] = False
#             del users[key]['password']
#             del users[key]['last_login']
#
#         next_page = page + 1 if users_count - (page + 1) * limit >= 0 else page
#         prev_page = page - 1 if page > 1 else 1
#         return Response({"count": users_count,
#                          "next": request.get_host() + "/api/users/?page=" + str(next_page) +
#                                  '&limit=' + str(limit),
#                          "previous": request.get_host() + "/api/users/?page=" + str(prev_page) +
#                                      '&limit=' + str(limit),
#                          "results": users}, 200)

#     def retrieve(self, request, *args, **kwargs):
#         curr_user = get_user(request, throw_exception=False)
#         subscribes = None
#
#         try:
#             instance = self.get_object()
#         except Http404:
#             return Response({"detail": "Страница не найдена."}, 404)
#
#         serializer = self.get_serializer(instance)
#         data = serializer.data
#
#         if not (curr_user is None):
#             if Subscribe.objects.filter(user=curr_user, subscribe=instance).exists():
#                 data["is_subscribed"] = True
#         if "is_subscribed" not in data:
#             data["is_subscribed"] = False
#
#
#         del data['password']
#         del data['last_login']
#
#         return Response(data, 200)

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

#     @action(methods=['get'], detail=False, url_path='me')
#     def me(self, request):
#         user = get_user(request)
#         if isinstance(user, Response):
#             return user
#         serializer = self.get_serializer(user)
#         data = serializer.data
#         data['is_subscribed'] = False
#         del data['password']
#         del data['last_login']
#         return Response(data, 200)
#
#     @action(methods=['put', 'delete'], detail=False, url_path='me/avatar')
#     def avatar(self, request):
#         if request.method == 'PUT':
#             try:
#                 data = json.loads(request.body)
#             except RequestDataTooBig:
#                 return Response({"avatar": ['Слишком большой вес фото']}, 400)
#             try:
#                 avatar = data['avatar']
#             except KeyError:
#                 return Response({"avatar": ["Загрузите аватар"]}, 400)
#             if not avatar:
#                 return Response({"avatar": ["Загрузите аватар"]}, 400)
#
#             ext = avatar.strip().split('data:image/')[1].split(';')[0]
#             if not (ext == 'png' or ext == 'jpg' or ext == 'jpeg'):
#                 return Response({"avatar": ['Аватар должен быть в формате png или jpg']}, 400)
#
#             user = get_user(request)
#             if isinstance(user, Response):
#                 return user
#             user.save_base64_image(avatar)
#
#             serializer = self.get_serializer(user)
#
#             return Response({"avatar": serializer.data['avatar']}, 200)
#         elif request.method == 'DELETE':
#             user = get_user(request)
#             if isinstance(user, Response):
#                 return user
#             old_filename = str(user.avatar).split('/')[-1]
#             if os.path.exists('/home/app/backend/media/img/avatar/' + old_filename) and old_filename:
#                 os.remove('/home/app/backend/media/img/avatar/' + old_filename)
#
#             user.avatar = None
#             user.save()
#
#             return Response({}, 204)
#
#     @action(methods=['post'], detail=False)
#     def set_password(self, request):
#         user = get_user(request)
#         if isinstance(user, Response):
#             return user
#
#         data = json.loads(request.body)
#         new_password = data['new_password']
#         current_password = data['current_password']
#
#         if not current_password:
#             return Response({"current_password": ["Введите текущий пароль"]}, 400)
#
#         if not check_password(current_password, user.password):
#             return Response({"current_password": ["Текущий пароль отличается от введенного"]}, 400)
#
#         try:
#             validate_password(new_password, user.username)
#         except ValidationError as e:
#             return Response({"new_password": e}, status=400)
#
#         user.password = make_password(new_password)
#         user.save()
#
#         return Response({}, 204)
#
#     @action(methods=['post', 'delete'], detail=False, url_path=r"(?P<pk>\d+)/subscribe")
#     def subscribe(self, request, *args, **kwargs):
#         if request.method == 'POST':
#             user = get_user(request)
#             if isinstance(user, Response):
#                 return user
#             limit = int(request.GET.get('recipes_limit', 3))
#             sub_user = self.get_object()
#             if Subscribe.objects.filter(user=user, subscribe=sub_user).exists():
#                 return Response({
#                     "detail": "Вы уже подписаны на этого пользователя"
#                 }, 400)
#             if sub_user.pk == user.pk:
#                 return Response({
#                     "detail": "Вы не можете подписаться на себя."
#                 }, 400)
#             subscribe = Subscribe(user=user, subscribe=sub_user)
#             subscribe.save()
#
#             data = self.get_serializer(sub_user).data
#             data['is_subscribed'] = True
#             recipes = Recipe.objects.filter(author=sub_user)[::-1]
#             recipes_count = len(recipes)
#             if len(recipes) > limit:
#                 recipes = recipes[:limit]
#             for i in range(len(recipes)):
#                 recipe_data = RecipeSerializer(recipes[i]).data
#                 recipes[i] = {
#                     "id": recipe_data['id'],
#                     "name": recipe_data['name'],
#                     "image": recipe_data['image'],
#                     "cooking_time": recipe_data['cooking_time']
#                 }
#             data['recipes_count'] = recipes_count
#             data['recipes'] = recipes
#
#             del data['password']
#             del data['last_login']
#
#             return Response(data, 201)
#         elif request.method == 'DELETE':
#             user = get_user(request)
#             if isinstance(user, Response):
#                 return user
#             sub_user = self.get_object()
#             if not Subscribe.objects.filter(user=user, subscribe=sub_user).exists():
#                 return Response({
#                     "detail": "Вы не были подписаны на этого пользователя"
#                 }, 400)
#
#             Subscribe.objects.get(user=user, subscribe=sub_user).delete()
#             return Response({}, 204)
#
#     @action(methods=['get'], detail=False)
#     def subscriptions(self, request, *args, **kwargs):
#         curr_user = get_user(request)
#         if isinstance(curr_user, Response):
#             return curr_user
#         page = request.GET.get('page', 1)
#         limit = request.GET.get('limit', 3)
#         recipes_limit = request.GET.get('recipes_limit', 3)
#         page = int(page)
#         limit = int(limit)
#         recipes_limit = int(recipes_limit)
#         users = [i.subscribe for i in Subscribe.objects.filter(user=curr_user)]
#         users_count = len(users)
#         users = users[limit * (page - 1):limit + (limit * (page - 1))]
#
#         serializer = self.get_serializer(users, many=True)
#         users = serializer.data
#         for key in range(0, len(users)):
#             users[key]['is_subscribed'] = True
#             del users[key]['password']
#             del users[key]['last_login']
#             recipes = Recipe.objects.filter(author_id=users[key]['id'])[::-1]
#             recipes_count = len(recipes)
#             if len(recipes) > recipes_limit:
#                 recipes = recipes[:recipes_limit]
#             for i in range(len(recipes)):
#                 recipe_data = RecipeSerializer(recipes[i]).data
#                 recipes[i] = {
#                     "id": recipe_data['id'],
#                     "name": recipe_data['name'],
#                     "image": recipe_data['image'],
#                     "cooking_time": recipe_data['cooking_time']
#                 }
#             users[key]['recipes_count'] = recipes_count
#             users[key]['recipes'] = recipes
#
#         next_page = page + 1 if users_count - (page + 1) * limit >= 0 else page
#         prev_page = page - 1 if page > 1 else 1
#         return Response({"count": users_count,
#                          "next": request.get_host() + "/api/users/subscriptions/?page=" + str(next_page) +
#                                  '&limit=' + str(limit) + '&recipes_limit=' + str(recipes_limit),
#                          "previous": request.get_host() + "/api/users/subscriptions/?page=" + str(prev_page) +
#                                      '&limit=' + str(limit) + '&recipes_limit=' + str(recipes_limit),
#                          "results": users}, 200)


@api_view(['POST'])
def login(request):
    data = request.data
    try:
        email = data['login']
    except KeyError:
        return Response({"login": ["Введите логин."]}, 400)
    try:
        password = data['password']
    except KeyError:
        return Response({"password": ["Введите пароль."]}, 400)

    if User.objects.filter(login=login).exists():
        user = User.objects.get(login=login)
        if check_password(password, user.password):
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
