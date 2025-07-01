from rest_framework import serializers
from .models import Province, Channel, Post, PlatformToken, Category
from django.contrib.auth import get_user_model

User = get_user_model()


class ProvinceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Province
        fields = '__all__'


class ChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = '__all__'


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = '__all__'
        extra_kwargs = {
            'created_by': {'read_only': True}  # فقط خواندنی باشه | خودمون توی perform_create ست می‌کنیم
        }


class PlatformTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlatformToken
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class CurrentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']