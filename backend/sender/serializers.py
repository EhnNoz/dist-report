from collections import Counter
from rest_framework import serializers
from .models import Province, Channel, Post, PlatformToken, Category
from django.contrib.auth import get_user_model
import pytz
from datetime import datetime
import jdatetime

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
    date = serializers.DateField(write_only=True)  # کاربر شمسی می‌فرسته، ولی اسمش date می‌مونه
    time = serializers.TimeField(write_only=True)
    channel_categories = serializers.SerializerMethodField()

    class Meta:
        model = Post
        exclude = ['scheduled_time']
        extra_kwargs = {
            'created_by': {'read_only': True},
        }

    def create(self, validated_data):
        jalali_date_str = validated_data.pop('date')  # رشته مثل "1404-01-16"
        time = validated_data.pop('time')

        # دستی تبدیل شمسی
        try:
            year, month, day = map(int, str(jalali_date_str).split('-'))
            jalali_date = jdatetime.date(year, month, day)
            gregorian_date = jalali_date.togregorian()
        except Exception as e:
            raise serializers.ValidationError({'date': 'تاریخ شمسی نامعتبر است.'})

        naive_datetime = datetime.combine(gregorian_date, time)
        tz = pytz.timezone('Asia/Tehran')
        validated_data['scheduled_time'] = tz.localize(naive_datetime)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'date' in validated_data or 'time' in validated_data:
            date_input = validated_data.get('date',
                                            instance.scheduled_time.astimezone(pytz.timezone('Asia/Tehran')).date())
            time = validated_data.get('time', instance.scheduled_time.astimezone(pytz.timezone('Asia/Tehran')).time())

            # اگر date یک رشته یا jdatetime.date باشد
            if isinstance(date_input, str):
                try:
                    year, month, day = map(int, date_input.split('-'))
                    jalali_date = jdatetime.date(year, month, day)
                    gregorian_date = jalali_date.togregorian()
                except:
                    raise serializers.ValidationError({'date': 'فرمت تاریخ شمسی نامعتبر است.'})
            elif isinstance(date_input, jdatetime.date):
                gregorian_date = date_input.togregorian()
            else:
                gregorian_date = date_input  # میلادی است

            naive_datetime = datetime.combine(gregorian_date, time)
            tz = pytz.timezone('Asia/Tehran')
            validated_data['scheduled_time'] = tz.localize(naive_datetime)

        return super().update(instance, validated_data)

    def get_channel_categories(self, obj):
        channels = obj.channels.all()
        categories = [channel.category.name for channel in channels if channel.category]
        if not categories:
            return []
        counter = Counter(categories)
        sorted_categories = sorted(counter.keys(), key=lambda x: counter[x], reverse=True)
        return sorted_categories

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.scheduled_time:
            tz = pytz.timezone('Asia/Tehran')
            localized_time = instance.scheduled_time.astimezone(tz)
            jalali_date = jdatetime.date.fromgregorian(date=localized_time.date())
            # تبدیل تاریخ به فرمت مورد نظر (مثلاً 1402-05-15)
            data['date'] = jalali_date.strftime('%Y-%m-%d')
            data['time'] = localized_time.time().strftime('%H:%M:%S')  # اگر می‌خواهید زمان هم فرمت شود
        return data




class PlatformTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlatformToken
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class CurrentUserSerializer(serializers.ModelSerializer):
    is_superadmin = serializers.BooleanField(source='is_superuser', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'is_superadmin']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_active', 'is_superuser']
