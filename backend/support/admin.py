from django.contrib import admin
from .models import Notification
from django.contrib.auth import get_user_model

User = get_user_model()

# Register your models here.
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_global', 'created_at', 'recipient_count')
    list_filter = ('is_global', 'created_at')
    search_fields = ('title', 'message')
    filter_horizontal = ('users',)
    fieldsets = (
        (None, {
            'fields': ('title', 'message')
        }),
        ('گیرندگان', {
            'fields': ('is_global', 'users')
        }),
    )
    readonly_fields = ('created_at',)

    def recipient_count(self, obj):
        if obj.is_global:
            return "همه کاربران"
        return obj.users.count()
    recipient_count.short_description = "تعداد گیرندگان"