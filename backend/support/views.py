from rest_framework import viewsets, status, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Ticket, TicketResponse, Notification
    # MemberProfile, GeneralNotice
from .serializers import TicketSerializer, TicketResponseSerializer, NotificationSerializer
    # GeneralNoticeSerializer
from django.contrib.auth import get_user_model
from .permissions import IsSuperUser, IsOwnerOrSuperUser
from rest_framework.viewsets import ViewSet
from django.db import models
# from .models import MemberProfile, GeneralNotice
# from .serializers import GeneralNoticeSerializer

User = get_user_model()


class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSuperUser]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Ticket.objects.all().order_by('-created_at')
        return Ticket.objects.filter(user=user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        ticket = self.get_object()
        user = request.user

        # کاربران عادی فقط می‌توانند به تیکت‌های خود پاسخ دهند
        if not user.is_staff and ticket.user != user:
            return Response(
                {"detail": "شما اجازه پاسخ به این تیکت را ندارید."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = TicketResponseSerializer(data=request.data)
        if serializer.is_valid():
            response = serializer.save(
                ticket=ticket,
                user=user,
                is_admin=user.is_staff
            )

            # اگر پاسخ از طرف ادمین بود، تیکت را به "در حال بررسی" تغییر وضعیت دهید
            if user.is_staff and ticket.status == 'open':
                ticket.status = 'in_progress'
                ticket.save()

            return Response(TicketResponseSerializer(response).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        ticket = self.get_object()
        user = request.user

        # فقط ادمین‌ها می‌توانند وضعیت تیکت را تغییر دهند
        if not user.is_staff:
            return Response(
                {"detail": "فقط ادمین‌ها می‌توانند وضعیت تیکت را تغییر دهند."},
                status=status.HTTP_403_FORBIDDEN
            )

        new_status = request.data.get('status')
        if new_status not in dict(Ticket.STATUS_CHOICES).keys():
            return Response(
                {"detail": "وضعیت نامعتبر است."},
                status=status.HTTP_400_BAD_REQUEST
            )

        ticket.status = new_status
        ticket.save()

        return Response(TicketSerializer(ticket).data)


class AdminTicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticated, IsSuperUser]  # فقط سوپر کاربر
    queryset = Ticket.objects.all().order_by('-created_at')

    @action(detail=True, methods=['post'])
    def add_admin_response(self, request, pk=None):
        ticket = self.get_object()
        response_text = request.data.get('response')

        if not response_text:
            return Response(
                {"detail": "متن پاسخ الزامی است."},
                status=status.HTTP_400_BAD_REQUEST
            )

        ticket.admin_response = response_text
        ticket.status = 'in_progress' if ticket.status == 'open' else ticket.status
        ticket.save()

        # ایجاد رکورد پاسخ
        TicketResponse.objects.create(
            ticket=ticket,
            user=request.user,
            message=response_text,
            is_admin=True
        )

        return Response(TicketSerializer(ticket).data)


class NotificationViewSet(ViewSet):
    permission_classes = [IsSuperUser]

    def list(self, request):
        """مشاهده تمام اعلان‌ها (فقط سوپر ادمین)"""
        notifications = Notification.objects.all().prefetch_related('users')
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)

    def create(self, request):
        """ایجاد اعلان جدید"""
        serializer = NotificationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        """مشاهده یک اعلان خاص"""
        try:
            notification = Notification.objects.get(pk=pk)
            serializer = NotificationSerializer(notification)
            return Response(serializer.data)
        except Notification.DoesNotExist:
            return Response({"error": "اعلان یافت نشد"}, status=status.HTTP_404_NOT_FOUND)

    def update(self, request, pk=None):
        """ویرایش یک اعلان"""
        try:
            notification = Notification.objects.get(pk=pk)
            serializer = NotificationSerializer(notification, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Notification.DoesNotExist:
            return Response({"error": "اعلان یافت نشد"}, status=status.HTTP_404_NOT_FOUND)

    def destroy(self, request, pk=None):
        """حذف یک اعلان"""
        try:
            notification = Notification.objects.get(pk=pk)
            notification.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Notification.DoesNotExist:
            return Response({"error": "اعلان یافت نشد"}, status=status.HTTP_404_NOT_FOUND)


class UserNotificationViewSet(ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        user = request.user
        notifications = Notification.objects.filter(
            models.Q(users=user) | models.Q(is_global=True)
        ).distinct().order_by('-created_at')
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)



class AllUsersViewSet(ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        user = request.user

        # 🔐 فقط سوپر ادمین میتونه این لیست رو ببینه
        if not user.is_superuser:
            raise PermissionDenied("شما دسترسی لازم برای مشاهده این بخش را ندارید.")

        # 📥 گرفتن همه کاربرها
        users = User.objects.all().order_by('-date_joined')

        # 📦 ساخت خروجی ساده (یا اگر سریالایزر داری، استفاده کن)
        result = [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_superuser": user.is_superuser,
                "date_joined": user.date_joined.isoformat(),
            }
            for user in users
        ]

        return Response(result)


# class GeneralNoticeViewSet(viewsets.ModelViewSet):
#     queryset = GeneralNotice.objects.all()
#     serializer_class = GeneralNoticeSerializer
#     permission_classes = [permissions.IsAuthenticated]
#
#     def get_queryset(self):
#         user = self.request.user
#
#         if not hasattr(user, 'memberprofile'):
#             return GeneralNotice.objects.none()  # یا raise یک ارور مناسب
#
#         user_profile = user.memberprofile
#         return GeneralNotice.objects.filter(receivers=user_profile) | GeneralNotice.objects.filter(
#             main_member=user_profile)
#
#     def create(self, request, *args, **kwargs):
#         sender_profile = request.user.memberprofile
#
#         # فقط اگر فرزند داشته باشه می‌تونه پیام بفرسته (سرگروه باشه)
#         if not sender_profile.children.exists():
#             return Response(
#                 {"error": "شما مجوز ارسال پیام ندارید."},
#                 status=status.HTTP_403_FORBIDDEN
#             )
#
#         receiver_ids = request.data.get("receivers", [])
#         receivers = MemberProfile.objects.filter(id__in=receiver_ids)
#
#         # فیلتر کردن فقط زیرمجموعه‌های مستقیم
#         valid_receivers = receivers.filter(id__in=sender_profile.children.values_list('id', flat=True))
#
#         if len(valid_receivers) != len(receiver_ids):
#             invalid = set(receiver_ids) - set(valid_receivers.values_list('id', flat=True))
#             return Response(
#                 {"error": f"شما مجوز ارسال به کاربران با IDهای {invalid} را ندارید."},
#                 status=status.HTTP_403_FORBIDDEN
#             )
#
#         # ایجاد اعلان جدید با main_member به جای sender
#         notice = GeneralNotice.objects.create(
#             main_member=sender_profile,
#             title=request.data.get("title"),
#             body=request.data.get("body")
#         )
#         notice.receivers.set(valid_receivers)
#         notice.save()
#
#         # سریالایز و پاسخ
#         serializer = self.get_serializer(notice)
#         return Response(serializer.data, status=status.HTTP_201_CREATED)







