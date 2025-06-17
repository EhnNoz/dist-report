from rest_framework import serializers
from .models import *
from .utils import to_jalali


class JalaliDateField(serializers.DateField):
    def to_representation(self, value):
        return to_jalali(value)


class JalaliDateTimeField(serializers.DateTimeField):
    def to_representation(self, value):
        return to_jalali(value)


class ProvinceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Province
        fields = ['id', 'name']

class PlatformSerializer(serializers.ModelSerializer):
    class Meta:
        model = Platform
        fields = ['id', 'name', 'logo']

class ChannelSerializer(serializers.ModelSerializer):
    province = ProvinceSerializer()
    platform = PlatformSerializer()

    class Meta:
        model = Channel
        fields = '__all__'

class TopChannelSerializer(serializers.ModelSerializer):
    latest_member = serializers.SerializerMethodField()
    total_posts = serializers.SerializerMethodField()
    total_views = serializers.SerializerMethodField()

    class Meta:
        model = Channel
        fields = ['name', 'latest_member', 'total_posts', 'total_views']

    def get_latest_member(self, obj):
        return obj.members.order_by('-collected_at').first().member_count if obj.members.exists() else 0

    def get_total_posts(self, obj):
        return obj.posts.count()

    def get_total_views(self, obj):
        return obj.posts.aggregate(total_views=models.Sum('views'))['total_views'] or 0


class PlatformStatsSerializer(serializers.Serializer):
    platform_id = serializers.IntegerField()
    platform_name = serializers.CharField()
    platform_logo = serializers.URLField()
    total_posts = serializers.IntegerField()
    total_views = serializers.IntegerField()


class ChannelStatsSerializer(serializers.Serializer):
    channel_id = serializers.IntegerField()
    channel_name = serializers.CharField()
    channel_picture = serializers.URLField(allow_null=True)
    total_posts = serializers.IntegerField()
    total_views = serializers.IntegerField()


class ChannelDetailSerializer(serializers.ModelSerializer):
    platform = PlatformSerializer()
    province = ProvinceSerializer()
    latest_member = serializers.SerializerMethodField()
    total_posts = serializers.SerializerMethodField()
    total_views = serializers.SerializerMethodField()
    # created_at = JalaliDateField()

    class Meta:
        model = Channel
        fields = [
            'name',
            'channel_id',
            'platform',
            'province',
            'topic',
            'sub_topic',
            'created_at',
            'picture',
            'latest_member',
            'total_posts',
            'total_views'
        ]

    def get_latest_member(self, obj):
        latest = obj.members.order_by('-collected_at').first()
        return latest.member_count if latest else 0

    def get_total_posts(self, obj):
        return obj.posts.count()

    def get_total_views(self, obj):
        return obj.posts.aggregate(total_views=models.Sum('views'))['total_views'] or 0


class AuthorStatsSerializer(serializers.Serializer):
    author_id = serializers.IntegerField()
    author_name = serializers.CharField()
    author_picture = serializers.URLField(allow_null=True, required=False)
    total_posts = serializers.IntegerField()
    total_views = serializers.IntegerField()


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['id', 'channel', 'author', 'post_text', 'hashtags', 'views', 'collected_at']
        # read_only_fields = ['collected_at']


class ChannelMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChannelMember
        fields = ['id', 'channel', 'member_count', 'collected_at']
        read_only_fields = ['collected_at']


class AuthorSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Author
        fields = ['id', 'name', 'family', 'full_name', 'national_code', 'expertise', 'profile_picture', 'created_at']
        read_only_fields = fields

    def get_full_name(self, obj):
        return f"{obj.name} {obj.family}"


class ChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = ['id', 'name', 'channel_id']


class MemberTrendSerializer(serializers.Serializer):
    date = serializers.DateField()
    total_members = serializers.IntegerField()

class MemberTrendChartSerializer(serializers.Serializer):
    categories = serializers.ListField(child=serializers.DateField(format='%Y-%m-%d'))
    data = serializers.ListField(child=serializers.IntegerField())
