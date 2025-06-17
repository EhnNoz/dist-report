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
    post_text = models.TextField("متن پست")
    hashtags = models.TextField("هشتگ‌ها")  # "tag1 tag2 tag3"
    author = models.ForeignKey('Author', on_delete=models.CASCADE, verbose_name="نویسنده")
    views = models.PositiveIntegerField("تعداد بازدید")
    collected_at = models.DateField("تاریخ جمع‌آوری")

    class Meta:
        verbose_name = "پست"
        verbose_name_plural = "پست‌ها"

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