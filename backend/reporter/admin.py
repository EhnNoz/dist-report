from django.contrib import admin
from .models import Channel, ChannelMember, Post, Author, Province, Platform

@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    readonly_fields = ('logo_preview',)

    def logo_preview(self, obj):
        return obj.logo.url if obj.logo else "-"
    logo_preview.short_description = "Logo Preview"


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'channel_id', 'platform', 'province', 'topic', 'created_at')
    list_filter = ('platform', 'province', 'topic')
    search_fields = ('name', 'channel_id')
    readonly_fields = ('picture_preview',)

    def picture_preview(self, obj):
        return obj.picture.url if obj.picture else "-"
    picture_preview.short_description = "Picture Preview"


@admin.register(ChannelMember)
class ChannelMemberAdmin(admin.ModelAdmin):
    list_display = ('channel', 'member_count', 'collected_at')
    list_filter = ('channel__platform', 'channel__province', 'collected_at')


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('channel', 'collected_at', 'views')
    list_filter = ('channel__platform', 'channel__province', 'collected_at')
    search_fields = ('post_text', 'hashtags')
