from collections import Counter
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q, Sum, Count, OuterRef, Subquery
from datetime import datetime
from .models import *
from .serializers import *
#from .permissions import IsAdminOrOwnProvince
# from rest_framework.filters import SearchFilter
from .permissions import CanAccessPanel
import jdatetime
from django_filters.rest_framework import DjangoFilterBackend


def parse_date(date_str):
    """تبدیل تاریخ با فرمت‌های مختلف (شمسی و میلادی) به date object"""
    # فرمت‌های میلادی
    # for fmt in ('%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y'):
    #     try:
    #         return datetime.strptime(date_str, fmt).date()
    #     except ValueError:
    #         continue

    # فرمت شمسی YYYY-MM-DD یا YYYY/MM/DD
    try:
        # جدا کردن سال، ماه و روز
        if '-' in date_str:
            y, m, d = map(int, date_str.split('-'))
        elif '/' in date_str:
            y, m, d = map(int, date_str.split('/'))
        else:
            raise ValueError("فرمت شمسی نامعتبر")

        # تبدیل شمسی به میلادی
        jalali_date = jdatetime.date(y, m, d)
        gregorian_date = jalali_date.togregorian()
        print(jalali_date)
        print(gregorian_date)
        return gregorian_date
    except Exception:
        pass

    return None


class DashboardViewSet(viewsets.ViewSet):
    # permission_classes = [IsAdminOrOwnProvince]
    # filter_backends = [SearchFilter]
    # search_fields = ['name', 'family', 'national_code', 'email', 'expertise']

    def list(self, request):
        user = request.user
        search_query = request.query_params.get('search', None)
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        platform_id = request.query_params.get('platform')
        province_id = request.query_params.get('province')
        author_id = request.query_params.get('author')
        channel_id = request.query_params.get('channel')

        filters = {}

        # 🔐 دسترسی کاربر عادی — فقط کانال(های) خودش را ببیند
        if not user.is_superuser:
            if not hasattr(user, 'userprofile') or not user.userprofile.channels.exists():
                return Response({"error": "شما به هیچ کانالی دسترسی ندارید."}, status=403)

            allowed_channel_ids = user.userprofile.channels.values_list('id', flat=True)
            filters['id__in'] = allowed_channel_ids

        # ✅ کاربر عادی هم می‌تونه از فیلترهای زیر استفاده کنه
        if province_id:
            filters['province_id'] = province_id
        if platform_id:
            filters['platform_id'] = platform_id
        if channel_id:
            filters['id'] = channel_id
        if author_id:
            filters['posts__author_id'] = author_id

        # 📦 داده‌های اصلی
        channels = Channel.objects.filter(**filters)
        posts = Post.objects.filter(channel__in=channels)

        if search_query:
            posts = posts.filter(
                Q(post_text__icontains=search_query) |
                Q(author__name__icontains=search_query) |
                Q(author__family__icontains=search_query) |
                Q(channel__name__icontains=search_query)
            ).distinct()

        # فیلتر تاریخ
        start_date_parsed = parse_date(start_date) if start_date else None
        end_date_parsed = parse_date(end_date) if end_date else None

        if start_date and end_date:
            if not start_date_parsed or not end_date_parsed:
                return Response(
                    {"error": "فرمت تاریخ نامعتبر است. استفاده از YYYY-MM-DD یا YYYY/MM/DD الزامی است."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            posts = posts.filter(collected_at__range=[start_date_parsed, end_date_parsed])

        # تعداد کل
        total_posts = posts.count()
        total_channels = channels.count()
        total_views = posts.aggregate(Sum('views'))['views__sum'] or 0

        # 👥 تعداد نویسندگان
        author_ids = posts.values_list('author', flat=True).distinct()
        authors = Author.objects.filter(id__in=author_ids)
        total_authors = authors.count()

        # 📈 روند انتشار
        # trend = posts.values('collected_at').annotate(count=Count('id').order_by('collected_at'))
        trend = (
            posts.values('collected_at')
                .annotate(count=Count('id'))
                .order_by('collected_at')  # ✅ اینجا داده‌ها به صورت صعودی سورت شدن
        )
        daily_trend = [{
            "categories": [item['collected_at'].strftime("%Y-%m-%d") for item in trend],
            "data": [item['count'] for item in trend]
        }]

        # 👁️ روند بازدید
        view_trend = (
            posts.values('collected_at')
                .annotate(total_views=Sum('views'))
                .order_by('collected_at')  # ✅ سورت به ترتیب صعودی
        )
        daily_view_trend = [{
            "categories": [item['collected_at'].strftime("%Y-%m-%d") for item in view_trend],
            "data": [item['total_views'] for item in view_trend]
        }]

        COLORS = [
            "#347928", "#C0EBA6", "#FFFBE6", "#FCCD2A", "#38C172",
            "#50C878", "#69B076", "#77DD77", "#88C999", "#A8D8B9"
        ]

        # 📊 کانال‌های برتر برحسب پست
        top_channels_by_post = Channel.objects.filter(**filters).annotate(
            post_count=Count('posts', filter=Q(posts__in=posts))
        ).order_by('-post_count')[:10]
        channel_categories = [c.name for c in top_channels_by_post]
        channel_data = [c.post_count for c in top_channels_by_post]
        series = [{"y": d, "color": COLORS[i % len(COLORS)]} for i, d in enumerate(channel_data)]
        top_channels_by_post = [{"categories": channel_categories, "data": series}]

        # 👁️ کانال‌های برتر برحسب بازدید
        top_channels_by_view = Channel.objects.filter(**filters).annotate(
            total_views=Sum('posts__views', filter=Q(posts__in=posts))
        ).order_by('-total_views')[:10]
        channel_categories = [c.name for c in top_channels_by_view]
        channel_data = [c.total_views for c in top_channels_by_view]
        series = [{"y": d, "color": COLORS[i % len(COLORS)]} for i, d in enumerate(channel_data)]
        top_channels_by_view = [{"categories": channel_categories, "data": series}]

        # 👤 نویسندگان - تعداد پست
        top_authors_by_post = authors.annotate(count=Count('post')).order_by('-count')[:10]
        series = [{"y": a.count, "color": COLORS[i % len(COLORS)]} for i, a in enumerate(top_authors_by_post)]
        top_authors_by_post = [{
            "categories": [a.name for a in top_authors_by_post],
            "data": series
        }]

        # 👁️ نویسندگان - مجموع بازدید
        author_views = {}
        for post in posts:
            if post.author_id:
                author_views[post.author_id] = author_views.get(post.author_id, 0) + post.views
        author_objects = {a.id: a for a in authors}
        sorted_author_views = sorted(
            [(aid, author_objects[aid].name, views) for aid, views in author_views.items()],
            key=lambda x: x[2], reverse=True
        )[:10]
        series = [{"y": v, "color": COLORS[i % len(COLORS)]} for i, (_, _, v) in enumerate(sorted_author_views)]
        top_authors_by_view = [{
            "categories": [n for _, n, _ in sorted_author_views],
            "data": series
        }]

        # 🔤 کلمات - فقط بر اساس انتشار
        word_list = []
        for p in posts:
            word_list.extend((p.post_text or "").split())
        word_freq = Counter(word_list).most_common(10)
        top_words_by_post = [{"name": w[0], "weight": w[1]} for w in word_freq]

        # #️⃣ هشتگ‌ها - فقط بر اساس انتشار
        hashtag_list = []
        for p in posts:
            hashtag_list.extend((p.hashtags or "").split())
        hashtag_freq = Counter(hashtag_list).most_common(10)
        top_hashtags_by_post = [{"name": h[0], "weight": h[1]} for h in hashtag_freq]

        # 📈 تعداد پست‌ها بر اساس پلتفرم
        # platform_post_counts = (
        #     channels.values('platform__name').annotate(count=Count('id')).order_by('-count')
        # )
        platform_post_counts = (
            Channel.objects.filter(**filters)
                .values('platform__name')
                .annotate(count=Count('posts', filter=Q(posts__in=posts)))
                .order_by('-count')
        )
        platform_post_counts_list = [{"name": item['platform__name'], "y": item['count']} for item in platform_post_counts]

        # 👁️ مجموع بازدیدها بر اساس پلتفرم
        # platform_total_views = (
        #     channels.values('platform__name').annotate(total_views=Sum('posts__views')).order_by('-total_views')
        # )
        platform_total_views = (
            Channel.objects.filter(**filters)
                .values('platform__name')
                .annotate(total_views=Sum('posts__views', filter=Q(posts__in=posts)))
                .order_by('-total_views')
        )
        platform_total_views_list = [
            {"name": item['platform__name'], "y": item['total_views'] or 0} for item in platform_total_views
        ]

        return Response({
            "total_posts": total_posts,
            "total_channels": total_channels,
            "total_views": total_views,
            "total_authors": total_authors,
            "daily_trend": daily_trend,
            "top_channels_by_post": top_channels_by_post,
            "top_channels_by_view": top_channels_by_view,
            "top_authors_by_post": top_authors_by_post,
            "top_authors_by_view": top_authors_by_view,
            "top_hashtags_by_post": top_hashtags_by_post,
            "top_words_by_post": top_words_by_post,
            "daily_view_trend": daily_view_trend,
            "platform_post_counts": platform_post_counts_list,
            "platform_total_views": platform_total_views_list
        })


class PlatformStatsViewSet(viewsets.ViewSet):
    def list(self, request):
        user = request.user
        search_query = request.query_params.get('search', None)
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        province_id = request.query_params.get('province')
        author_id = request.query_params.get('author')
        channel_id = request.query_params.get('channel')

        filters = {}

        # 🔐 دسترسی کاربر عادی — فقط کانال(های) خودش را ببیند
        if not user.is_superuser:
            if not hasattr(user, 'userprofile') or not user.userprofile.channels.exists():
                return Response({"error": "شما به هیچ کانالی دسترسی ندارید."}, status=403)

            allowed_channel_ids = user.userprofile.channels.values_list('id', flat=True)
            filters['id__in'] = allowed_channel_ids

        # ✅ کاربر عادی هم می‌تونه از فیلترهای زیر استفاده کنه
        if province_id:
            filters['province_id'] = province_id
        if author_id:
            filters['posts__author_id'] = author_id
        if channel_id:
            filters['id'] = channel_id

        channels = Channel.objects.filter(**filters)
        posts = Post.objects.filter(channel__in=channels)

        if search_query:
            posts = posts.filter(
                Q(post_text__icontains=search_query) |
                Q(author__name__icontains=search_query) |
                Q(author__family__icontains=search_query) |
                Q(channel__name__icontains=search_query)
            ).distinct()

        start_date_parsed = parse_date(start_date) if start_date else None
        end_date_parsed = parse_date(end_date) if end_date else None

        if start_date and end_date:
            if not start_date_parsed or not end_date_parsed:
                return Response(
                    {"error": "فرمت تاریخ نامعتبر است. استفاده از YYYY-MM-DD یا YYYY/MM/DD الزامی است."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            posts = posts.filter(collected_at__range=[start_date_parsed, end_date_parsed])

        total_posts = posts.count()
        total_views = posts.aggregate(Sum('views'))['views__sum'] or 0

        platforms = Platform.objects.all()
        result = []

        for platform in platforms:
            platform_channels = channels.filter(platform=platform)
            platform_posts = posts.filter(channel__in=platform_channels)

            platform_total_posts = platform_posts.count()
            platform_total_views = platform_posts.aggregate(Sum('views'))['views__sum'] or 0

            logo_url = request.build_absolute_uri(platform.logo.url) if platform.logo else None

            result.append({
                "platform_id": platform.id,
                "platform_name": platform.name,
                "platform_logo": logo_url,
                "total_posts": platform_total_posts,
                "total_views": platform_total_views
            })

        return Response(result)


class ChannelStatsViewSet(viewsets.ViewSet):
    # permission_classes = [IsAdminOrOwnProvince]

    def list(self, request):
        user = request.user
        search_query = request.query_params.get('search', None)
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        platform_id = request.query_params.get('platform')
        province_id = request.query_params.get('province')
        author_id = request.query_params.get('author')
        channel_id = request.query_params.get('channel')

        filters = {}

        # 🔐 دسترسی کاربر عادی — فقط کانال(های) خودش را ببیند
        if not user.is_superuser:
            if not hasattr(user, 'userprofile') or not user.userprofile.channels.exists():
                return Response({"error": "شما به هیچ کانالی دسترسی ندارید."}, status=403)

            allowed_channel_ids = user.userprofile.channels.values_list('id', flat=True)
            filters['id__in'] = allowed_channel_ids

        # ✅ کاربر عادی هم می‌تونه از فیلترهای زیر استفاده کنه
        if province_id:
            filters['province_id'] = province_id
        if platform_id:
            filters['platform_id'] = platform_id
        if author_id:
            filters['posts__author_id'] = author_id
        if channel_id:
            filters['id'] = channel_id

        channels = Channel.objects.filter(**filters)
        result = []

        for channel in channels:
            posts = Post.objects.filter(channel=channel)

            if search_query:
                posts = posts.filter(
                    Q(post_text__icontains=search_query) |
                    Q(author__name__icontains=search_query) |
                    Q(author__family__icontains=search_query) |
                    Q(channel__name__icontains=search_query)
                ).distinct()

            start_date_parsed = parse_date(start_date) if start_date else None
            end_date_parsed = parse_date(end_date) if end_date else None

            if start_date and end_date:
                if not start_date_parsed or not end_date_parsed:
                    return Response(
                        {"error": "فرمت تاریخ نامعتبر است. استفاده از YYYY-MM-DD یا YYYY/MM/DD الزامی است."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                posts = posts.filter(collected_at__range=[start_date_parsed, end_date_parsed])

            total_posts = posts.count()
            total_views = posts.aggregate(Sum('views'))['views__sum'] or 0

            picture_url = request.build_absolute_uri(channel.picture.url) if channel.picture else None

            result.append({
                "channel_id": channel.id,
                "channel_name": channel.name,
                "channel_picture": picture_url,
                "total_posts": total_posts,
                "total_views": total_views
            })

        return Response(result)


class ChannelListViewSet(viewsets.ViewSet):
    # permission_classes = [IsAdminOrOwnProvince]

    def list(self, request):
        user = request.user
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        platform_id = request.query_params.get('platform')
        province_id = request.query_params.get('province')
        author_id = request.query_params.get('author')
        channel_id = request.query_params.get('channel')

        filters = {}

        # 🔐 دسترسی کاربر عادی — فقط کانال(های) خودش را ببیند
        if not user.is_superuser:
            if not hasattr(user, 'userprofile') or not user.userprofile.channels.exists():
                return Response({"error": "شما به هیچ کانالی دسترسی ندارید."}, status=403)

            allowed_channel_ids = user.userprofile.channels.values_list('id', flat=True)
            filters['id__in'] = allowed_channel_ids

        # ✅ کاربر عادی هم می‌تونه از فیلترهای زیر استفاده کنه
        if province_id:
            filters['province_id'] = province_id
        if platform_id:
            filters['platform_id'] = platform_id
        if author_id:
            filters['posts__author_id'] = author_id
        if channel_id:
            filters['id'] = channel_id

        channels = Channel.objects.filter(**filters).prefetch_related('members', 'posts')

        # فیلتر بر اساس بازه زمانی (در صورت وجود)
        start_date_parsed = parse_date(start_date) if start_date else None
        end_date_parsed = parse_date(end_date) if end_date else None

        if start_date and end_date:
            if not start_date_parsed or not end_date_parsed:
                return Response(
                    {"error": "فرمت تاریخ نامعتبر است. استفاده از YYYY-MM-DD یا YYYY/MM/DD الزامی است."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            posts = Post.objects.filter(channel__in=channels, collected_at__range=[start_date_parsed, end_date_parsed])
            channels = Channel.objects.filter(posts__in=posts).distinct()

        serializer = ChannelDetailSerializer(channels.distinct(), many=True)
        return Response(serializer.data)


class AuthorStatsViewSet(viewsets.ViewSet):
    # permission_classes = [IsAdminOrOwnProvince]

    def list(self, request):
        user = request.user
        search_query = request.query_params.get('search', None)
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        platform_id = request.query_params.get('platform')
        province_id = request.query_params.get('province')
        channel_id = request.query_params.get('channel')

        filters = {}

        # 🔐 دسترسی کاربر عادی — فقط کانال(های) خودش را ببیند
        if not user.is_superuser:
            if not hasattr(user, 'userprofile') or not user.userprofile.channels.exists():
                return Response({"error": "شما به هیچ کانالی دسترسی ندارید."}, status=403)

            allowed_channel_ids = user.userprofile.channels.values_list('id', flat=True)
            filters['channel__in'] = allowed_channel_ids

        # ✅ کاربر عادی هم می‌تونه از فیلترهای زیر استفاده کنه
        if province_id:
            filters['channel__province_id'] = province_id
        if platform_id:
            filters['channel__platform_id'] = platform_id
        if channel_id:
            filters['channel__id'] = channel_id

        # 📦 فیلتر پست‌ها بر اساس دسترسی و فیلترهای کاربر
        posts = Post.objects.filter(**filters)

        if search_query:
            posts = posts.filter(
                Q(post_text__icontains=search_query) |
                Q(author__name__icontains=search_query) |
                Q(author__family__icontains=search_query) |
                Q(channel__name__icontains=search_query)
            ).distinct()

        # فیلتر تاریخ
        start_date_parsed = parse_date(start_date) if start_date else None
        end_date_parsed = parse_date(end_date) if end_date else None

        if start_date and end_date:
            if not start_date_parsed or not end_date_parsed:
                return Response(
                    {"error": "فرمت تاریخ نامعتبر است. استفاده از YYYY-MM-DD یا YYYY/MM/DD الزامی است."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            posts = posts.filter(collected_at__range=[start_date_parsed, end_date_parsed])

        # 👤 آمار نویسندگان
        author_ids = posts.values_list('author', flat=True).distinct()
        authors = Author.objects.filter(id__in=author_ids)

        result = []
        COLORS = [
            "#347928", "#C0EBA6", "#FFFBE6", "#FCCD2A", "#38C172",
            "#50C878", "#69B076", "#77DD77", "#88C999", "#A8D8B9"
        ]

        for idx, author in enumerate(authors):
            author_posts = posts.filter(author=author)
            total_posts = author_posts.count()
            total_views = author_posts.aggregate(Sum('views'))['views__sum'] or 0

            picture_url = request.build_absolute_uri(author.profile_picture.url) if author.profile_picture else None

            result.append({
                "author_id": author.id,
                "author_name": author.full_name,
                "author_picture": picture_url,
                "total_posts": total_posts,
                "total_views": total_views,
                "color": COLORS[idx % len(COLORS)]
            })

        # مرتب‌سازی بر اساس تعداد پست
        result = sorted(result, key=lambda x: x['total_posts'], reverse=True)

        return Response(result)


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [CanAccessPanel]


class ChannelMemberViewSet(viewsets.ModelViewSet):
    queryset = ChannelMember.objects.all()
    serializer_class = ChannelMemberSerializer
    permission_classes = [CanAccessPanel]


class ReadOnlyAuthorViewSet(viewsets.ViewSet):
    # permission_classes = [IsAuthenticated]  # فقط کاربران لاگین‌کرده
    serializer_class = AuthorSerializer
    permission_classes = [CanAccessPanel]

    def list(self, request):
        queryset = Author.objects.all()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        try:
            author = Author.objects.get(pk=pk)
            serializer = self.serializer_class(author)
            return Response(serializer.data)
        except Author.DoesNotExist:
            return Response({"error": "نویسنده یافت نشد"}, status=404)


class ReadOnlyChannelViewSet(viewsets.ViewSet):
    # permission_classes = [IsAuthenticated]  # فقط کاربران لاگین‌کرده
    serializer_class = ChannelSerializer
    permission_classes = [CanAccessPanel]

    def list(self, request):
        queryset = Channel.objects.all()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        try:
            author = Channel.objects.get(pk=pk)
            serializer = self.serializer_class(author)
            return Response(serializer.data)
        except Channel.DoesNotExist:
            return Response({"error": "نویسنده یافت نشد"}, status=404)


class ChannelMemberTrendViewSet(viewsets.ViewSet):
    def list(self, request):
        user = request.user
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        platform_id = request.query_params.get('platform')
        province_id = request.query_params.get('province')
        channel_id = request.query_params.get('channel')  # ✅ فیلتر کانال

        filters = {}

        # 🔐 دسترسی کاربر عادی — فقط کانال(های) خودش را ببیند
        if not user.is_superuser:
            if not hasattr(user, 'userprofile') or not user.userprofile.channels.exists():
                return Response({"error": "شما به هیچ کانالی دسترسی ندارید."}, status=403)

            allowed_channel_ids = user.userprofile.channels.values_list('id', flat=True)
            filters['id__in'] = allowed_channel_ids

        # ✅ کاربر عادی هم می‌تونه از فیلترهای زیر استفاده کنه
        if province_id:
            filters['province_id'] = province_id
        if platform_id:
            filters['platform_id'] = platform_id
        if channel_id:
            filters['id'] = channel_id  # فقط یک کانال خاص

        # ✅ گرفتن کانال‌های فیلتر شده
        channels = Channel.objects.filter(**filters).distinct()

        # ✅ گرفتن عضویت‌ها با فیلتر کانال
        members = ChannelMember.objects.filter(channel__in=Subquery(channels.values('id')))

        # ✅ فیلتر تاریخ
        start_date_parsed = parse_date(start_date) if start_date else None
        end_date_parsed = parse_date(end_date) if end_date else None

        if start_date and end_date:
            if not start_date_parsed or not end_date_parsed:
                return Response(
                    {"error": "فرمت تاریخ نامعتبر است. استفاده از YYYY-MM-DD یا YYYY/MM/DD الزامی است."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            members = members.filter(collected_at__range=[start_date_parsed, end_date_parsed])

        # ✅ گرفتن آخرین member_count در هر روز برای هر کانال
        latest_member_per_day = (
            ChannelMember.objects
            .filter(
                channel=OuterRef('channel'),
                collected_at=OuterRef('collected_at')
            )
            .order_by('-id')  # فرض: id بالاتر = آخرین داده
        )

        # ✅ فقط آخرین داده در هر روز برای هر کانال
        daily_last_members = (
            ChannelMember.objects
            .filter(id=Subquery(latest_member_per_day.values('id')[:1]))
            .order_by('collected_at', 'channel')
        )

        # ✅ اعمال فیلتر کانال/استان/پلتفرم روی آخرین ممبرها
        daily_last_members = daily_last_members.filter(channel__in=channels)

        # ✅ گروه‌بندی بر اساس تاریخ و محاسبه مجموع
        trend_data = {}
        for obj in daily_last_members:
            key = obj.collected_at.strftime("%Y-%m-%d")
            if key not in trend_data:
                trend_data[key] = []
            trend_data[key].append(obj.member_count)

        result = []
        categories = []
        data = []

        for date_str, counts in sorted(trend_data.items()):
            total = sum(counts)  # یا max(counts) اگر منظورت جمع نباشه
            result.append({
                "date": date_str,
                "total_members": total
            })
            categories.append(date_str)
            data.append(total)

        chart_format = [{
            "categories": categories,
            "data": data
        }]

        total_members = 0
        if result:
            total_members = result[-1]['total_members']  # آخرین روز

        print(total_members)

        return Response({
            "trend": result,
            "chart": chart_format,
            "total_members": total_members
        })


class UserLastPostsViewSet(viewsets.ViewSet):
    """
    نمایش پست‌های کاربر با تمام فیلترهای ممکن
    """

    def list(self, request):
        user = request.user

        # 🔐 بررسی دسترسی کاربر به کانال‌ها
        if not hasattr(user, 'userprofile') or not user.userprofile.channels.exists():
            return Response(
                {"error": "شما به هیچ کانالی دسترسی ندارید."},
                status=status.HTTP_403_FORBIDDEN
            )

        # 🎯 دریافت تمام پارامترهای فیلتر
        search_query = request.query_params.get('search')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        platform_id = request.query_params.get('platform')
        province_id = request.query_params.get('province')
        author_id = request.query_params.get('author')
        channel_id = request.query_params.get('channel')

        # 🛡️ فیلترهای پایه - فقط کانال‌های مجاز کاربر
        base_filters = {
            'channel__in': user.userprofile.channels.all()
        }

        # ➕ افزودن فیلترهای اختیاری
        if channel_id:
            base_filters['channel__id'] = channel_id
        if author_id:
            base_filters['author__id'] = author_id
        if platform_id:
            base_filters['channel__platform__id'] = platform_id
        if province_id:
            base_filters['channel__province__id'] = province_id

        # 📝 دریافت پست‌ها با فیلترهای پایه
        posts = Post.objects.filter(**base_filters)

        # 🔍 فیلتر جستجو (اگر وجود دارد)
        if search_query:
            posts = posts.filter(
                Q(post_text__icontains=search_query) |
                Q(hashtags__icontains=search_query) |
                Q(author__name__icontains=search_query) |
                Q(author__family__icontains=search_query) |
                Q(channel__name__icontains=search_query)
            ).distinct()

        # 📅 فیلتر تاریخ (اگر وجود دارد)
        start_date_parsed = parse_date(start_date) if start_date else None
        end_date_parsed = parse_date(end_date) if end_date else None

        if start_date and end_date:
            if not start_date_parsed or not end_date_parsed:
                return Response(
                    {"error": "فرمت تاریخ نامعتبر است. استفاده از YYYY-MM-DD یا YYYY/MM/DD الزامی است."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            posts = posts.filter(collected_at__range=[start_date_parsed, end_date_parsed])

        # محاسبه آمار قبل از محدود کردن
        total_posts = posts.count()
        total_views = posts.aggregate(Sum('views'))['views__sum'] or 0

        # مرتب‌سازی و محدود کردن نتایج
        posts = posts.select_related(
            'channel',
            'author',
            'channel__platform',
            'channel__province'
        ).order_by('-collected_at')[:10]  # 10 پست آخر

        serializer = PostSerializer(posts, many=True)

        return Response({
            "total_posts": total_posts,
            "total_views": total_views,
            "filters": {
                "platform": platform_id,
                "province": province_id,
                "author": author_id,
                "channel": channel_id,
                "start_date": start_date,
                "end_date": end_date,
                "search_query": search_query
            },
            "posts": serializer.data
        })


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorUpdateSerializer
    permission_classes = [CanAccessPanel]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name', 'family', 'username']


