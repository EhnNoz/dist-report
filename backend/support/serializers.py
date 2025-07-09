from rest_framework import serializers
from .models import Ticket, TicketResponse, Notification
    # , MemberProfile, GeneralNotice
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']


class TicketResponseSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = TicketResponse
        fields = ['id', 'user', 'message', 'created_at', 'is_admin']
        read_only_fields = ['id', 'user', 'created_at', 'is_admin']


class TicketSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    responses = TicketResponseSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)

    class Meta:
        model = Ticket
        fields = [
            'id', 'user', 'subject', 'message', 'status',
            'status_display', 'priority', 'priority_display',
            'created_at', 'updated_at', 'admin_response', 'responses'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'responses']


class NotificationSerializer(serializers.ModelSerializer):
    users = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)

    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'users', 'is_global', 'created_at']
        read_only_fields = ['created_at']

    def create(self, validated_data):
        users = validated_data.pop('users', [])
        notification = Notification.objects.create(**validated_data)

        if not notification.is_global:
            notification.users.set(users)
        else:
            notification.users.clear()  # اگر global باشه، users نادیده گرفته بشن

        return notification

    def update(self, instance, validated_data):
        users = validated_data.pop('users', None)
        instance.title = validated_data.get('title', instance.title)
        instance.message = validated_data.get('message', instance.message)
        instance.is_global = validated_data.get('is_global', instance.is_global)
        instance.save()

        if not instance.is_global and users is not None:
            instance.users.set(users)
        elif instance.is_global:
            instance.users.clear()

        return instance


# class MemberProfileSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = MemberProfile
#         fields = ['id', 'user']


# class GeneralNoticeSerializer(serializers.ModelSerializer):
#     receivers = MemberProfileSerializer(many=True, read_only=True)
#
#     class Meta:
#         model = GeneralNotice
#         fields = '__all__'


