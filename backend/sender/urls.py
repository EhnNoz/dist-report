from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'provinces', views.ProvinceViewSet, basename='provinces')
router.register(r'channels', views.ChannelViewSet, basename='channels')
router.register(r'send-posts', views.PostViewSet, basename='send-posts')
router.register(r'category', views.CategoryViewSet, basename='category')
router.register(r'platform-token', views.PlatformTokenViewSet, basename='platform-token')
router.register('current-user', views.CurrentUserViewSet, basename='current-user')

urlpatterns = [
    path('', include(router.urls)),
]