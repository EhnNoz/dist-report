from django.contrib import admin
from .models import Province, Channel, Post, Category, PlatformToken
from django import forms
from django.core.exceptions import ValidationError


@admin.register(PlatformToken)
class PlatformTokenAdmin(admin.ModelAdmin):
    list_display = ['platform', 'token', 'is_active']
    list_editable = ['is_active']
    fieldsets = (
        (None, {
            'fields': ('platform', 'token', 'is_active')
        }),
    )
    list_filter = ['is_active', 'platform']


class PostAdminForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        channels = cleaned_data.get('channels')
        category = cleaned_data.get('category')

        if not channels and not category:
            raise ValidationError("لطفاً یا کانال‌ها را انتخاب کنید یا یک دسته‌بندی را مشخص کنید.")

        if channels and category:
            raise ValidationError("فقط می‌توانید یا کانال‌ها را انتخاب کنید یا یک دسته‌بندی، نه هر دو را با هم.")

        if category and not Channel.objects.filter(category=category, users=self.request.user).exists():
            raise ValidationError("هیچ کانالی در این دسته‌بندی وجود ندارد که به شما دسترسی داشته باشد.")

        return cleaned_data


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ['name', 'province', 'platform']


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    form = PostAdminForm
    list_display = ['caption', 'scheduled_time', 'sent']
    filter_horizontal = ['channels']
    exclude = ['created_by']

    fieldsets = (
        (None, {
            'fields': ('caption', 'media', 'scheduled_time')
        }),
        ('انتخاب دسته‌بندی', {
            'fields': ('category',),
            'description': 'با انتخاب یک دسته‌بندی، پست به تمام کانال‌های مربوط به آن دسته‌بندی و دسترسی شما ارسال می‌شود.'
        }),
        ('کانال‌ها (فقط اگر دسته‌بندی انتخاب نشود)', {
            'fields': ('channels',)
        }),
    )

    def save_model(self, request, obj, form, change):
        # تنظیم created_by
        if not obj.pk:
            obj.created_by = request.user

        super().save_model(request, obj, form, change)

        # اگر دسته‌بندی انتخاب شده باشد، کانال‌های مجاز را تنظیم کن
        if obj.category:
            channels_in_category = Channel.objects.filter(
                category=obj.category,
                users=request.user  # فقط کانال‌هایی که کاربر به آن‌ها دسترسی دارد
            )
            obj.channels.set(channels_in_category)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        obj = form.instance
        if obj.category:
            channels_in_category = Channel.objects.filter(
                category=obj.category,
                users=request.user
            )
            obj.channels.set(channels_in_category)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(created_by=request.user)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "channels":
            # فقط کانال‌هایی که کاربر به آن‌ها دسترسی دارد
            kwargs["queryset"] = Channel.objects.filter(users=request.user)
            # اختیاری کردن فیلد (چون یا کانال‌ها یا دسته‌بندی انتخاب میشه)
            kwargs["required"] = False
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # ارسال request به فرم
        form.request = request
        return form