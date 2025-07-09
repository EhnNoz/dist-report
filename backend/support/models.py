from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Ticket(models.Model):
    STATUS_CHOICES = (
        ('open', 'باز'),
        ('in_progress', 'در حال بررسی'),
        ('resolved', 'حل شده'),
        ('closed', 'بسته شده'),
    )
    PRIORITY_CHOICES = (
        ('low', 'کم'),
        ('medium', 'متوسط'),
        ('high', 'بالا'),
        ('critical', 'بحرانی'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets', verbose_name="کاربر")
    subject = models.CharField("موضوع", max_length=200)
    message = models.TextField("پیام")
    status = models.CharField("وضعیت", max_length=20, choices=STATUS_CHOICES, default='open')
    priority = models.CharField("اولویت", max_length=20, choices=PRIORITY_CHOICES, default='medium')
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("تاریخ بروزرسانی", auto_now=True)
    admin_response = models.TextField("پاسخ ادمین", blank=True, null=True)

    class Meta:
        verbose_name = "تیکت"
        verbose_name_plural = "تیکت‌ها"
        ordering = ['-created_at']

    def __str__(self):
        return f"تیکت #{self.id} - {self.subject}"


class TicketResponse(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='responses', verbose_name="تیکت")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="کاربر")
    message = models.TextField("پیام")
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    is_admin = models.BooleanField("پاسخ ادمین", default=False)

    class Meta:
        verbose_name = "پاسخ تیکت"
        verbose_name_plural = "پاسخ‌های تیکت"
        ordering = ['created_at']

    def __str__(self):
        return f"پاسخ برای تیکت #{self.ticket.id}"


class Notification(models.Model):
    title = models.CharField("عنوان", max_length=255)
    message = models.TextField("محتوا")
    created_at = models.DateTimeField(auto_now_add=True)

    users = models.ManyToManyField(
        User,
        blank=True,
        related_name='notifications',
        verbose_name="کاربران مقصد"
    )
    is_global = models.BooleanField(default=False, verbose_name="ارسال به همه")

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']


# class Role(models.Model):
#     name = models.CharField(max_length=50)
#
#     def __str__(self):
#         return self.name
#
#
# class MemberProfile(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)
#     parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
#
#     def __str__(self):
#         return f"{self.user.username} - {self.role.name if self.role else 'No Role'}"
#
#
# class GeneralNotice(models.Model):
#     main_member = models.ForeignKey(MemberProfile, on_delete=models.CASCADE, related_name='sent_notices')
#     receivers = models.ManyToManyField(MemberProfile, related_name='received_notices', blank=True)
#     title = models.CharField(max_length=200)
#     body = models.TextField()
#     created_at = models.DateTimeField(auto_now_add=True)
#
#     def __str__(self):
#         return f"{self.main_member} → {self.title}"