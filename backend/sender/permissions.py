# permissions.py
from rest_framework import permissions


class IsOwnerProvince(permissions.BasePermission):
    """
    اجازه دسترسی فقط به داده‌های استان کاربر
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        user_province = request.user.province
        requested_province = request.query_params.get('province', None)

        # اگر استان مشخص شده باشد، باید با استان کاربر یکی باشد
        if requested_province:
            return requested_province == str(user_province)
        else:
            # اگر استان مشخص نشده باشد، فقط داده‌های استان کاربر قابل دسترسی است
            return True