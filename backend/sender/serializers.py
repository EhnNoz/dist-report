from collections import Counter
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
    channel_categories = serializers.SerializerMethodField()

    # published_at_shamsi = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Post
        fields = '__all__'
        extra_kwargs = {
            'created_by': {'read_only': True}  # فقط خواندنی باشه | خودمون توی perform_create ست می‌کنیم
        }

    def get_channel_categories(self, obj):
        # 1. تمام کانال‌های این پست رو بگیر
        channels = obj.channels.all()

        # 2. فقط کانال‌هایی که دارای category هستند رو فیلتر کن
        categories = [
            channel.category.name for channel in channels
            if channel.category
        ]

        # 3. اگر هیچ دسته‌بندی‌ای وجود نداشت
        if not categories:
            return []

        # 4. شمارش تعداد تکرار هر category
        counter = Counter(categories)

        # 5. مرتب‌سازی بر اساس تعداد تکرار (از زیاد به کم)
        sorted_categories = sorted(counter.keys(), key=lambda x: counter[x], reverse=True)

        return sorted_categories




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


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_active', 'is_superuser']
