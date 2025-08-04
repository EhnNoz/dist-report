from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator


# مدل ۱: کانال
class Channel(models.Model):
    name = models.CharField("نام کانال", max_length=255)
    channel_id = models.CharField("آیدی کانال", max_length=100, unique=True)
    platform = models.ForeignKey('Platform', on_delete=models.CASCADE, verbose_name="پلتفرم")
    province = models.ForeignKey('Province', on_delete=models.CASCADE, verbose_name="استان")
    topic = models.CharField("موضوع", max_length=100)
    sub_topic = models.CharField("زیر موضوع", max_length=100)
    audience = models.CharField("مخاطب", max_length=100)
    created_at = models.DateField("تاریخ ایجاد")
    picture = models.ImageField("عکس کانال", upload_to='channel_pictures/', null=True, blank=True)

    class Meta:
        verbose_name = "کانال"
        verbose_name_plural = "کانال‌ها"

    def __str__(self):
        return self.name

# مدل ۲: عضویت کانال
class ChannelMember(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='members', verbose_name="کانال")
    member_count = models.PositiveIntegerField("تعداد عضو")
    collected_at = models.DateField("تاریخ جمع‌آوری")

    class Meta:
        verbose_name = "عضویت کانال"
        verbose_name_plural = "عضویت کانال‌ها"

    # def __str__(self):
    #     return self.channel

# مدل ۳: پست کانال
class Post(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='posts', verbose_name="کانال")
    # platform = models.CharField("platform", max_length=100, null=True, blank=True)
    post_text = models.TextField("متن پست", null=True, blank=True)
    hashtags = models.TextField("هشتگ‌ها", null=True, blank=True)  # "tag1 tag2 tag3"
    author = models.ForeignKey('Author', on_delete=models.CASCADE, verbose_name="نویسنده")
    # views = models.PositiveIntegerField("تعداد بازدید")
    # collected_at = models.DateField("تاریخ جمع‌آوری")

    # فیلدهای جدید
    update_id = models.PositiveIntegerField("Update ID", null=True, blank=True)
    message_id = models.PositiveIntegerField("Message ID", null=True, blank=True)
    chat_id = models.CharField("Chat ID", max_length=100, null=True, blank=True)
    chat_type = models.CharField("Chat Type", max_length=50, null=True, blank=True)

    sender_id = models.BigIntegerField("Sender ID", null=True, blank=True)
    sender_is_bot = models.BooleanField("Is Bot", default=False)
    sender_name = models.CharField("Sender Name", max_length=255, null=True, blank=True)
    sender_username = models.CharField("Sender Username", max_length=255, null=True, blank=True)

    has_media = models.BooleanField("دارای مدیا", default=False)

    # Photo Fields
    photo_file_id = models.CharField("Photo File ID", max_length=500, null=True, blank=True)
    photo_file_unique_id = models.CharField("Photo Unique ID", max_length=255, null=True, blank=True)
    photo_width = models.PositiveIntegerField("Photo Width", null=True, blank=True)
    photo_height = models.PositiveIntegerField("Photo Height", null=True, blank=True)
    photo_file_size = models.PositiveIntegerField("Photo File Size", null=True, blank=True)

    # Video Fields
    video_file_id = models.CharField("Video File ID", max_length=500, null=True, blank=True)
    video_file_unique_id = models.CharField("Video Unique ID", max_length=255, null=True, blank=True)
    video_width = models.PositiveIntegerField("Video Width", null=True, blank=True)
    video_height = models.PositiveIntegerField("Video Height", null=True, blank=True)
    video_duration = models.PositiveIntegerField("Video Duration", null=True, blank=True)
    video_file_size = models.PositiveIntegerField("Video File Size", null=True, blank=True)

    # Document Fields
    document_file_id = models.CharField("Document File ID", max_length=500, null=True, blank=True)
    document_file_unique_id = models.CharField("Document Unique ID", max_length=255, null=True, blank=True)
    document_file_name = models.CharField("Document File Name", max_length=255, null=True, blank=True)
    document_mime_type = models.CharField("Document MIME Type", max_length=100, null=True, blank=True)
    document_file_size = models.PositiveIntegerField("Document File Size", null=True, blank=True)

    # Forward Info
    forward_from_id = models.BigIntegerField("Forward From ID", null=True, blank=True)
    forward_from_name = models.CharField("Forward From Name", max_length=255, null=True, blank=True)
    forward_from_username = models.CharField("Forward From Username", max_length=255, null=True, blank=True)
    forward_date = models.DateTimeField("Forward Date", null=True, blank=True)

    forward_from_chat_id = models.CharField("Forward From Chat ID", max_length=100, null=True, blank=True)
    forward_from_chat_title = models.CharField("Forward From Chat Title", max_length=255, null=True, blank=True)
    forward_from_chat_username = models.CharField("Forward From Chat Username", max_length=255, null=True, blank=True)
    forward_from_message_id = models.PositiveIntegerField("Forward From Message ID", null=True, blank=True)

    forward_origin_type = models.CharField("Forward Origin Type", max_length=50, null=True, blank=True)
    forward_origin_sender_id = models.BigIntegerField("Forward Origin Sender ID", null=True, blank=True)
    forward_origin_sender_name = models.CharField("Forward Origin Sender Name", max_length=255, null=True, blank=True)

    entities = models.JSONField("Entities", null=True, blank=True)  # برای ذخیره لیست entityها
    reply_to_message_id = models.PositiveIntegerField("Reply To Message ID", null=True, blank=True)

    views = models.PositiveIntegerField("تعداد بازدید", default=0)
    collected_at = models.DateField("تاریخ جمع‌آوری")

    # ✅ فیلد جدید: date - تاریخ ارسال پیام در تلگرام
    date = models.DateTimeField("تاریخ ارسال پیام", null=True, blank=True)



    class Meta:
        verbose_name = "پست"
        verbose_name_plural = "پست‌ها"
        # unique_together = ['channel', 'date', 'post_text', 'hashtags']

    def __str__(self):
        return self.hashtags

# مدل ۴: نویسنده


# مدل ۵: استان
class Province(models.Model):
    name = models.CharField("نام استان", max_length=100)

    class Meta:
        verbose_name = "استان"
        verbose_name_plural = "استان‌ها"

    def __str__(self):
        return self.name

# مدل ۶: پلتفرم
class Platform(models.Model):
    name = models.CharField("نام پلتفرم", max_length=100)
    logo = models.ImageField("لوگو", upload_to='platform_logos/')

    class Meta:
        verbose_name = "پلتفرم"
        verbose_name_plural = "پلتفرم‌ها"

    def __str__(self):
        return self.name


class Author(models.Model):
    GENDER_CHOICES = (
        ('male', 'مرد'),
        ('female', 'زن'),
    )

    name = models.CharField("نام", max_length=100)
    family = models.CharField("نام خانوادگی", max_length=100)
    username = models.CharField("نام کاربری", max_length=100)
    national_code = models.CharField(
        "کد ملی",
        max_length=10,
        validators=[
            RegexValidator(r'^\d{10}$', 'کد ملی باید ۱۰ رقم باشد.')
        ],
        unique=True,
        null=True,
        blank=True
    )
    birth_date = models.DateField("تاریخ تولد", null=True, blank=True)
    gender = models.CharField("جنسیت", max_length=10, choices=GENDER_CHOICES, default='other')
    phone = models.CharField(
        "شماره تماس",
        max_length=15,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'فرمت شماره تماس نامعتبر است.')],
        null=True,
        blank=True
    )
    email = models.EmailField("ایمیل", null=True, blank=True)
    address = models.TextField("آدرس", null=True, blank=True)
    province = models.ForeignKey(Province, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="استان")
    # city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="شهر")
    postal_code = models.CharField("کد پستی", max_length=20, null=True, blank=True)
    profile_picture = models.ImageField("عکس پروفایل", upload_to='authors/', null=True, blank=True)
    bio = models.TextField("بیوگرافی", null=True, blank=True)
    expertise = models.CharField("زمینه فعالیت/تخصص", max_length=255, null=True, blank=True)
    is_active = models.BooleanField("فعال", default=True)
    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین بروزرسانی", auto_now=True)

    class Meta:
        verbose_name = "نویسنده"
        verbose_name_plural = "نویسندگان"

    def __str__(self):
        return f"{self.name} {self.family}"

    @property
    def full_name(self):
        return f"{self.name} {self.family}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    channels = models.ManyToManyField('Channel', blank=True, verbose_name="کانال‌های مرتبط")
    can_access_panel = models.BooleanField("دسترسی به پنل", default=False)

    class Meta:
        verbose_name = "دسترسی پنل"
        verbose_name_plural = "دسترسی پنل"

    def __str__(self):
        return self.user.username


# class UserChannelAccess(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
#
#     class Meta:
#         unique_together = ('user', 'channel')
#
#
# class UserAuthorAccess(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     author = models.ForeignKey(Author, on_delete=models.CASCADE)
#
#     class Meta:
#         unique_together = ('user', 'author')


