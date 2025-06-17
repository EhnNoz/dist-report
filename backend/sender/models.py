from django.db import models
from django.contrib.auth.models import User
from django_jalali.db import models as jmodels
import os
from django.core.exceptions import ValidationError


class PlatformToken(models.Model):
    PLATFORM_CHOICES = [
        ('telegram', 'Telegram'),
        ('bale', 'Bale'),
        ('eitaa', 'Eitaa'),
    ]
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, unique=True, verbose_name="پلتفرم")
    token = models.CharField(max_length=100, verbose_name="توکن API")
    is_active = models.BooleanField(default=True, verbose_name="فعال/غیرفعال")

    def __str__(self):
        return f"{self.get_platform_display()} - {self.token}"

    class Meta:
        verbose_name = "توکن پلتفرم"
        verbose_name_plural = "توکن‌های پلتفرم"


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام دسته")

    class Meta:
        verbose_name = "دسته بندی"
        verbose_name_plural = "دسته بندی ها"

    def __str__(self):
        return self.name


class Province(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "مرکز"
        verbose_name_plural = "مراکز"

    def __str__(self):
        return self.name

class Channel(models.Model):
    PLATFORM_CHOICES = [
        ('telegram', 'Telegram'),
        ('bale', 'Bale'),
        ('eitaa', 'Eitaa'),
    ]
    name = models.CharField(max_length=100)
    channel_id = models.CharField(max_length=100)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    province = models.ForeignKey(Province, on_delete=models.CASCADE)
    users = models.ManyToManyField(User, related_name='allowed_channels', blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="دسته‌بندی")
    # allowed_users = models.ManyToManyField(User, related_name='allowed_channels')

    class Meta:
        verbose_name = "کانال"
        verbose_name_plural = "کانال ها"

    def __str__(self):
        return f"{self.name} ({self.platform}) ({self.channel_id}) ({self.category})"


def validate_media(value):
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mkv', '.mov', '.avi']
    ext = os.path.splitext(value.name)[1].lower()

    if ext not in valid_extensions:
        raise ValidationError("فرمت فایل نامعتبر است.")

    max_size = 15 * 1024 * 1024  # 15 MB
    if value.size > max_size:
        raise ValidationError(f"حجم فایل نباید بیشتر از 15 مگابایت باشد. حجم فعلی: {value.size / (1024 * 1024):.2f} MB")


class Post(models.Model):
    # titr = models.CharField(
    #     max_length=255,
    #     blank=True,
    #     null=True,
    #     verbose_name="عنوان"
    # )
    caption = models.TextField(verbose_name="پیام")
    # author = models.CharField(
    #     max_length=100,
    #     blank=True,
    #     null=True,
    #     verbose_name="نویسنده"
    # )
    #
    # hashtags = models.TextField(
    #     blank=True,
    #     null=True,
    #     help_text="هر هشتگ در یک خط و با فاصله جدا شوند.",
    #     verbose_name="هشتگ‌ها"
    # )

    # image = models.ImageField(upload_to='posts/',verbose_name="عکس", blank=True, null=True)
    # video = models.FileField(upload_to='posts/videos/', verbose_name="ویدئو", blank=True, null=True)
    media = models.FileField(
        upload_to='posts/media/',
        verbose_name="تصویر یا ویدئو",
        blank=True,
        null=True,
        validators=[validate_media]  # اعتبارسنجی فایل
    )
    scheduled_time = models.DateTimeField(verbose_name="زمانبندی")
    # scheduled_time = jmodels.jDateTimeField()
    channels = models.ManyToManyField(Channel, verbose_name="انتخاب کانال")
    sent = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="ارسال به تمام کانال‌های دسته‌بندی"
    )

    class Meta:
        verbose_name = "پست"
        verbose_name_plural = "پست ها"

    def __str__(self):
        return self.caption[:20]