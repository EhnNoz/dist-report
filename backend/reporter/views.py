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
    def list(self, request):
        user = request.user
        search_query = request.query_params.get('search', None)
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # ✅ خواندن پارامترها به صورت comma-separated
        platform_str = request.query_params.get('platform', '')
        province_str = request.query_params.get('province', '')
        author_str = request.query_params.get('author', '')
        channel_str = request.query_params.get('channel', '')

        # 🧹 تبدیل رشته "1,2,3" به لیست اعداد
        def parse_ids(s):
            if not s.strip():
                return []
            try:
                return [int(x.strip()) for x in s.split(',') if x.strip().isdigit()]
            except ValueError:
                return []

        platform_ids = parse_ids(platform_str)
        province_ids = parse_ids(province_str)
        author_ids = parse_ids(author_str)
        channel_ids = parse_ids(channel_str)

        filters = {}

        # 🔐 دسترسی کاربر عادی — فقط کانال(های) خودش را ببیند
        if not user.is_superuser:
            if not hasattr(user, 'userprofile') or not user.userprofile.channels.exists():
                return Response({"error": "شما به هیچ کانالی دسترسی ندارید."}, status=403)

            allowed_channel_ids = set(user.userprofile.channels.values_list('id', flat=True))
            filters['id__in'] = allowed_channel_ids

        # ✅ اعمال فیلترهای چندتایی با __in
        if province_ids:
            filters['province_id__in'] = province_ids

        if platform_ids:
            filters['platform_id__in'] = platform_ids

        if channel_ids:
            requested_channel_ids = set(channel_ids)
            if 'id__in' in filters:
                valid_channels = filters['id__in'] & requested_channel_ids
                if not valid_channels:
                    return Response(
                        {"error": "کانال‌های انتخاب شده یا وجود ندارند یا دسترسی ندارید."},
                        status=400
                    )
                filters['id__in'] = list(valid_channels)
            else:
                filters['id__in'] = list(requested_channel_ids)

        if author_ids:
            filters['posts__author_id__in'] = author_ids

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

        # 📅 فیلتر تاریخ
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
        post_author_ids = posts.values_list('author', flat=True).distinct()
        authors = Author.objects.filter(id__in=post_author_ids)
        total_authors = authors.count()

        # 📈 روند انتشار
        trend = (
            posts.values('collected_at')
            .annotate(count=Count('id'))
            .order_by('collected_at')
        )
        daily_trend = [{
            "categories": [item['collected_at'].strftime("%Y-%m-%d") for item in trend],
            "data": [item['count'] for item in trend],
            "color": "#b2532f"
        }]

        # 👁️ روند بازدید
        view_trend = (
            posts.values('collected_at')
            .annotate(total_views=Sum('views'))
            .order_by('collected_at')
        )
        daily_view_trend = [{
            "categories": [item['collected_at'].strftime("%Y-%m-%d") for item in view_trend],
            "data": [item['total_views'] for item in view_trend],
            "color": "#b2532f"
        }]

        # COLORS = [
        #     "#347928", "#C0EBA6", "#FFFBE6", "#FCCD2A", "#38C172",
        #     "#50C878", "#69B076", "#77DD77", "#88C999", "#A8D8B9"
        # ]

        COLORS = [
            "#9b4929", "#b2532f", "#fe7743", "#fe8e63", "#feb092",
            "#ffc7b2", "#fff1ec", "#fff1ec", "#fff1ec", "#fff1ec"
        ]

        # 📊 کانال‌های برتر برحسب پست
        top_channels_by_post_qs = Channel.objects.filter(**filters).annotate(
            post_count=Count('posts', filter=Q(posts__in=posts))
        ).order_by('-post_count')[:10]
        channel_categories = [c.name for c in top_channels_by_post_qs]
        channel_data = [c.post_count for c in top_channels_by_post_qs]
        series = [{"y": d, "color": COLORS[i % len(COLORS)]} for i, d in enumerate(channel_data)]
        top_channels_by_post = [{"categories": channel_categories, "data": series}]

        # 👁️ کانال‌های برتر برحسب بازدید
        top_channels_by_view_qs = Channel.objects.filter(**filters).annotate(
            total_views=Sum('posts__views', filter=Q(posts__in=posts))
        ).order_by('-total_views')[:10]
        channel_categories = [c.name for c in top_channels_by_view_qs]
        channel_data = [c.total_views for c in top_channels_by_view_qs]
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
        #     Channel.objects.filter(**filters)
        #     .values('platform__name')
        #     .annotate(count=Count('posts', filter=Q(posts__in=posts)))
        #     .order_by('-count')
        # )
        # platform_post_counts_list = [
        #     {"name": item['platform__name'], "y": item['count']} for item in platform_post_counts
        # ]

        platform_post_counts = (
            Channel.objects.filter(**filters)
                .values('platform__name')
                .annotate(count=Count('posts', filter=Q(posts__in=posts)))
                .order_by('-count')
        )

        platform_post_counts_list = [
            {
                "name": item['platform__name'],
                "y": item['count'],
                "color": COLORS[i % len(COLORS)]
            }
            for i, item in enumerate(platform_post_counts)
        ]

        # 👁️ مجموع بازدیدها بر اساس پلتفرم
        # platform_total_views = (
        #     Channel.objects.filter(**filters)
        #     .values('platform__name')
        #     .annotate(total_views=Sum('posts__views', filter=Q(posts__in=posts)))
        #     .order_by('-total_views')
        # )
        # platform_total_views_list = [
        #     {"name": item['platform__name'], "y": item['total_views'] or 0} for item in platform_total_views
        # ]
        platform_total_views = (
            Channel.objects.filter(**filters)
                .values('platform__name')
                .annotate(total_views=Sum('posts__views', filter=Q(posts__in=posts)))
                .order_by('-total_views')
        )

        platform_total_views_list = [
            {
                "name": item['platform__name'],
                "y": item['total_views'] or 0,
                "color": COLORS[i % len(COLORS)]
            }
            for i, item in enumerate(platform_total_views)
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

        # ✅ خواندن پارامترها به صورت comma-separated
        province_str = request.query_params.get('province', '')
        author_str = request.query_params.get('author', '')
        channel_str = request.query_params.get('channel', '')

        # 🧹 تابع کمکی برای تبدیل "1,2,3" به لیست عدد
        def parse_ids(s):
            if not s.strip():
                return []
            try:
                return [int(x.strip()) for x in s.split(',') if x.strip().isdigit()]
            except ValueError:
                return []

        province_ids = parse_ids(province_str)
        author_ids = parse_ids(author_str)
        channel_ids = parse_ids(channel_str)

        filters = {}

        # 🔐 دسترسی کاربر عادی — فقط کانال(های) خودش را ببیند
        if not user.is_superuser:
            if not hasattr(user, 'userprofile') or not user.userprofile.channels.exists():
                return Response({"error": "شما به هیچ کانالی دسترسی ندارید."}, status=403)

            allowed_channel_ids = set(user.userprofile.channels.values_list('id', flat=True))
            filters['id__in'] = allowed_channel_ids

        # 🧩 اعمال فیلترهای چندتایی با __in
        if province_ids:
            filters['province_id__in'] = province_ids

        if author_ids:
            filters['posts__author_id__in'] = author_ids

        if channel_ids:
            requested_channel_ids = set(channel_ids)
            if 'id__in' in filters:
                valid_channels = filters['id__in'] & requested_channel_ids
                if not valid_channels:
                    return Response(
                        {"error": "کانال‌های انتخاب شده یا وجود ندارند یا دسترسی ندارید."},
                        status=400
                    )
                filters['id__in'] = list(valid_channels)
            else:
                filters['id__in'] = list(requested_channel_ids)

        # ✅ فیلتر کانال‌ها
        channels = Channel.objects.filter(**filters).distinct()
        posts = Post.objects.filter(channel__in=channels)

        # 🔍 جستجو
        if search_query:
            posts = posts.filter(
                Q(post_text__icontains=search_query) |
                Q(author__name__icontains=search_query) |
                Q(author__family__icontains=search_query) |
                Q(channel__name__icontains=search_query)
            ).distinct()

        # 📅 فیلتر تاریخ
        start_date_parsed = parse_date(start_date) if start_date else None
        end_date_parsed = parse_date(end_date) if end_date else None

        if start_date and end_date:
            if not start_date_parsed or not end_date_parsed:
                return Response(
                    {"error": "فرمت تاریخ نامعتبر است. استفاده از YYYY-MM-DD یا YYYY/MM/DD الزامی است."},
                    status=400
                )
            posts = posts.filter(collected_at__range=[start_date_parsed, end_date_parsed])

        # 📊 محاسبه آمار بر اساس پلتفرم
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

        # ✅ خروجی دقیقاً مثل قبل: فقط یک لیست
        return Response(result)

class ChannelStatsViewSet(viewsets.ViewSet):
    def list(self, request):
        user = request.user
        search_query = request.query_params.get('search', None)
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # ✅ خواندن پارامترها به صورت comma-separated
        province_str = request.query_params.get('province', '')
        platform_str = request.query_params.get('platform', '')
        author_str = request.query_params.get('author', '')
        channel_str = request.query_params.get('channel', '')

        # 🧹 تابع کمکی برای تبدیل "1,2,3" به لیست عدد
        def parse_ids(s):
            if not s.strip():
                return []
            try:
                return [int(x.strip()) for x in s.split(',') if x.strip().isdigit()]
            except ValueError:
                return []

        province_ids = parse_ids(province_str)
        platform_ids = parse_ids(platform_str)
        author_ids = parse_ids(author_str)
        channel_ids = parse_ids(channel_str)

        filters = {}

        # 🔐 دسترسی کاربر عادی — فقط کانال(های) خودش را ببیند
        if not user.is_superuser:
            if not hasattr(user, 'userprofile') or not user.userprofile.channels.exists():
                return Response({"error": "شما به هیچ کانالی دسترسی ندارید."}, status=403)

            allowed_channel_ids = set(user.userprofile.channels.values_list('id', flat=True))
            filters['id__in'] = allowed_channel_ids

        # 🧩 اعمال فیلترهای چندتایی با __in
        if province_ids:
            filters['province_id__in'] = province_ids

        if platform_ids:
            filters['platform_id__in'] = platform_ids

        if author_ids:
            filters['posts__author_id__in'] = author_ids

        if channel_ids:
            requested_channel_ids = set(channel_ids)
            if 'id__in' in filters:
                valid_channels = filters['id__in'] & requested_channel_ids
                if not valid_channels:
                    return Response(
                        {"error": "کانال‌های انتخاب شده یا وجود ندارند یا دسترسی ندارید."},
                        status=400
                    )
                filters['id__in'] = list(valid_channels)
            else:
                filters['id__in'] = list(requested_channel_ids)

        # ✅ فیلتر کانال‌ها
        channels = Channel.objects.filter(**filters).distinct()
        result = []

        # 📅 فیلتر تاریخ
        start_date_parsed = parse_date(start_date) if start_date else None
        end_date_parsed = parse_date(end_date) if end_date else None

        if start_date and end_date:
            if not start_date_parsed or not end_date_parsed:
                return Response(
                    {"error": "فرمت تاریخ نامعتبر است. استفاده از YYYY-MM-DD یا YYYY/MM/DD الزامی است."},
                    status=400
                )

        # 📊 محاسبه آمار برای هر کانال
        for channel in channels:
            posts = Post.objects.filter(channel=channel)

            # 🔎 جستجو
            if search_query:
                posts = posts.filter(
                    Q(post_text__icontains=search_query) |
                    Q(author__name__icontains=search_query) |
                    Q(author__family__icontains=search_query) |
                    Q(channel__name__icontains=search_query)
                ).distinct()

            # 📅 فیلتر تاریخ
            if start_date_parsed and end_date_parsed:
                posts = posts.filter(collected_at__range=[start_date_parsed, end_date_parsed])

            total_posts = posts.count()
            total_views = posts.aggregate(Sum('views'))['views__sum'] or 0

            picture_url = request.build_absolute_uri(channel.picture.url) if channel.picture else None

            result.append({
                "channel_id": channel.id,
                "channel_name": channel.name,
                "channel_picture": picture_url,
                "total_posts": total_posts,
                "total_views": total_views,
            })

        # ✅ خروجی کاملاً بدون تغییر — مثل قبل
        return Response(result)

class ChannelListViewSet(viewsets.ViewSet):
    def list(self, request):
        user = request.user
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # ✅ خواندن پارامترها به صورت comma-separated
        province_str = request.query_params.get('province', '')
        platform_str = request.query_params.get('platform', '')
        author_str = request.query_params.get('author', '')
        channel_str = request.query_params.get('channel', '')

        # 🧹 تابع کمکی برای تبدیل "1,2,3" به لیست عدد
        def parse_ids(s):
            if not s.strip():
                return []
            try:
                return [int(x.strip()) for x in s.split(',') if x.strip().isdigit()]
            except ValueError:
                return []

        province_ids = parse_ids(province_str)
        platform_ids = parse_ids(platform_str)
        author_ids = parse_ids(author_str)
        channel_ids = parse_ids(channel_str)

        filters = {}

        # 🔐 دسترسی کاربر عادی — فقط کانال(های) خودش را ببیند
        if not user.is_superuser:
            if not hasattr(user, 'userprofile') or not user.userprofile.channels.exists():
                return Response({"error": "شما به هیچ کانالی دسترسی ندارید."}, status=403)

            allowed_channel_ids = set(user.userprofile.channels.values_list('id', flat=True))
            filters['id__in'] = allowed_channel_ids

        # 🧩 اعمال فیلترهای چندتایی با __in
        if province_ids:
            filters['province_id__in'] = province_ids

        if platform_ids:
            filters['platform_id__in'] = platform_ids

        if author_ids:
            filters['posts__author_id__in'] = author_ids

        if channel_ids:
            requested_channel_ids = set(channel_ids)
            if 'id__in' in filters:
                valid_channels = filters['id__in'] & requested_channel_ids
                if not valid_channels:
                    return Response(
                        {"error": "کانال‌های انتخاب شده یا وجود ندارند یا دسترسی ندارید."},
                        status=400
                    )
                filters['id__in'] = list(valid_channels)
            else:
                filters['id__in'] = list(requested_channel_ids)

        # ⏳ مرحله ۱: فیلتر کانال‌ها بر اساس دسترسی و فیلترهای کاربر
        channels = Channel.objects.filter(**filters).prefetch_related('members', 'posts').distinct()

        # 📅 مرحله ۲: فیلتر تاریخ (اگر مشخص شده باشد)
        start_date_parsed = parse_date(start_date) if start_date else None
        end_date_parsed = parse_date(end_date) if end_date else None

        if start_date and end_date:
            if not start_date_parsed or not end_date_parsed:
                return Response(
                    {"error": "فرمت تاریخ نامعتبر است. استفاده از YYYY-MM-DD یا YYYY/MM/DD الزامی است."},
                    status=400
                )

            # پست‌های فیلتر شده در بازه زمانی
            posts_in_range = Post.objects.filter(
                channel__in=channels,
                collected_at__range=[start_date_parsed, end_date_parsed]
            )

            # فقط کانال‌هایی که در آن بازه پست داشتن
            channels = channels.filter(posts__in=posts_in_range).distinct()

        # ✅ سریالایز و خروجی — کاملاً بدون تغییر
        serializer = ChannelDetailSerializer(channels, many=True)
        return Response(serializer.data)


class AuthorStatsViewSet(viewsets.ViewSet):
    def list(self, request):
        user = request.user
        search_query = request.query_params.get('search', None)
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # ✅ خواندن پارامترها به صورت comma-separated
        province_str = request.query_params.get('province', '')
        platform_str = request.query_params.get('platform', '')
        channel_str = request.query_params.get('channel', '')

        # 🧹 تابع کمکی برای تبدیل "1,2,3" به لیست عدد
        def parse_ids(s):
            if not s.strip():
                return []
            try:
                return [int(x.strip()) for x in s.split(',') if x.strip().isdigit()]
            except ValueError:
                return []

        province_ids = parse_ids(province_str)
        platform_ids = parse_ids(platform_str)
        channel_ids = parse_ids(channel_str)

        filters = {}

        # 🔐 دسترسی کاربر عادی — فقط کانال(های) خودش را ببیند
        if not user.is_superuser:
            if not hasattr(user, 'userprofile') or not user.userprofile.channels.exists():
                return Response({"error": "شما به هیچ کانالی دسترسی ندارید."}, status=403)

            allowed_channel_ids = set(user.userprofile.channels.values_list('id', flat=True))
            filters['channel__in'] = allowed_channel_ids

        # 🧩 اعمال فیلترهای چندتایی با __in
        if province_ids:
            filters['channel__province_id__in'] = province_ids

        if platform_ids:
            filters['channel__platform_id__in'] = platform_ids

        if channel_ids:
            requested_channel_ids = set(channel_ids)
            if 'channel__in' in filters:
                valid_channels = filters['channel__in'] & requested_channel_ids
                if not valid_channels:
                    return Response(
                        {"error": "کانال‌های انتخاب شده یا وجود ندارند یا دسترسی ندارید."},
                        status=400
                    )
                filters['channel__in'] = list(valid_channels)
            else:
                filters['channel__in'] = list(requested_channel_ids)

        # 📦 فیلتر پست‌ها
        posts = Post.objects.filter(**filters)

        # 🔍 جستجو
        if search_query:
            posts = posts.filter(
                Q(post_text__icontains=search_query) |
                Q(author__name__icontains=search_query) |
                Q(author__family__icontains=search_query) |
                Q(channel__name__icontains=search_query)
            ).distinct()

        # 📅 فیلتر تاریخ
        start_date_parsed = parse_date(start_date) if start_date else None
        end_date_parsed = parse_date(end_date) if end_date else None

        if start_date and end_date:
            if not start_date_parsed or not end_date_parsed:
                return Response(
                    {"error": "فرمت تاریخ نامعتبر است. استفاده از YYYY-MM-DD یا YYYY/MM/DD الزامی است."},
                    status=400
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
                "author_name": getattr(author, 'full_name', f"{author.name} {author.family}"),
                "author_picture": picture_url,
                "total_posts": total_posts,
                "total_views": total_views,
                "color": COLORS[idx % len(COLORS)]
            })

        # مرتب‌سازی بر اساس تعداد پست — مثل قبل
        result = sorted(result, key=lambda x: x['total_posts'], reverse=True)

        # ✅ خروجی دقیقاً مثل قبل: یک لیست از نویسندگان
        return Response(result)


class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [CanAccessPanel]

    def get_queryset(self):
        queryset = Post.objects.all()

        # تابع کمکی برای تبدیل "1,2,3" به لیست اعداد
        def parse_ids(param):
            if not param:
                return None
            try:
                return [int(x.strip()) for x in param.split(',') if x.strip().isdigit()]
            except ValueError:
                return []

        # فیلتر بر اساس channel (آی‌دی کانال)
        channel_param = self.request.query_params.get('channel', None)
        channel_ids = parse_ids(channel_param)
        if channel_ids:
            queryset = queryset.filter(channel_id__in=channel_ids)

        # فیلتر بر اساس platform (آی‌دی پلتفرم)
        platform_param = self.request.query_params.get('platform', None)
        platform_ids = parse_ids(platform_param)
        if platform_ids:
            queryset = queryset.filter(channel__platform_id__in=platform_ids)

        return queryset


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
    serializer_class = ChannelSerializer
    permission_classes = [CanAccessPanel]

    def list(self, request):
        queryset = Channel.objects.all()

        # اضافه کردن فیلتر platform اگر در query_params باشد
        platform = request.query_params.get('platform')
        if platform is not None:
            queryset = queryset.filter(platform=platform)

        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        try:
            # ابتدا چنل را با pk می‌گیریم
            channel = Channel.objects.get(pk=pk)

            # بررسی فیلتر platform
            platform = request.query_params.get('platform')
            if platform is not None and str(channel.platform.id) != str(platform):
                return Response({"error": "چنل مورد نظر با پلتفرم مشخص شده مطابقت ندارد."}, status=404)

            serializer = self.serializer_class(channel)
            return Response(serializer.data)
        except Channel.DoesNotExist:
            return Response({"error": "نویسنده یافت نشد"}, status=404)


class ChannelMemberTrendViewSet(viewsets.ViewSet):
    def list(self, request):
        user = request.user
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # ✅ خواندن پارامترها به صورت comma-separated
        province_str = request.query_params.get('province', '')
        platform_str = request.query_params.get('platform', '')
        channel_str = request.query_params.get('channel', '')

        # 🧹 تابع کمکی برای تبدیل "1,2,3" به لیست عدد
        def parse_ids(s):
            if not s.strip():
                return []
            try:
                return [int(x.strip()) for x in s.split(',') if x.strip().isdigit()]
            except ValueError:
                return []

        province_ids = parse_ids(province_str)
        platform_ids = parse_ids(platform_str)
        channel_ids = parse_ids(channel_str)

        filters = {}

        # 🔐 دسترسی کاربر عادی — فقط کانال(های) خودش را ببیند
        if not user.is_superuser:
            if not hasattr(user, 'userprofile') or not user.userprofile.channels.exists():
                return Response({"error": "شما به هیچ کانالی دسترسی ندارید."}, status=403)

            allowed_channel_ids = set(user.userprofile.channels.values_list('id', flat=True))
            filters['id__in'] = allowed_channel_ids

        # 🧩 اعمال فیلترهای چندتایی با __in
        if province_ids:
            filters['province_id__in'] = province_ids

        if platform_ids:
            filters['platform_id__in'] = platform_ids

        if channel_ids:
            requested_channel_ids = set(channel_ids)
            if 'id__in' in filters:
                valid_channels = filters['id__in'] & requested_channel_ids
                if not valid_channels:
                    return Response(
                        {"error": "کانال‌های انتخاب شده یا وجود ندارند یا دسترسی ندارید."},
                        status=400
                    )
                filters['id__in'] = list(valid_channels)
            else:
                filters['id__in'] = list(requested_channel_ids)

        # ✅ اعمال فیلترها روی کانال‌ها
        channels = Channel.objects.filter(**filters).distinct()

        if not channels.exists():
            return Response({
                "trend": [],
                "chart": [{"categories": [], "data": []}],
                "total_members": 0
            })

        # 📅 فیلتر تاریخ
        start_date_parsed = parse_date(start_date) if start_date else None
        end_date_parsed = parse_date(end_date) if end_date else None

        if start_date and end_date:
            if not start_date_parsed or not end_date_parsed:
                return Response(
                    {"error": "فرمت تاریخ نامعتبر است. استفاده از YYYY-MM-DD یا YYYY/MM/DD الزامی است."},
                    status=400
                )

        # 🔍 فیلتر اولیه روی ChannelMember
        members = ChannelMember.objects.filter(channel__in=channels)

        if start_date_parsed and end_date_parsed:
            members = members.filter(collected_at__range=[start_date_parsed, end_date_parsed])

        # ✅ گرفتن آخرین رکورد عضویت در هر روز (بر اساس id)
        latest_per_day_subquery = ChannelMember.objects.filter(
            channel=OuterRef('channel'),
            collected_at=OuterRef('collected_at')
        ).order_by('-id')

        daily_latest = ChannelMember.objects.filter(
            id=Subquery(latest_per_day_subquery.values('id')[:1])
        ).filter(channel__in=channels)

        if start_date_parsed and end_date_parsed:
            daily_latest = daily_latest.filter(collected_at__range=[start_date_parsed, end_date_parsed])

        # 📊 گروه‌بندی بر اساس تاریخ و جمع member_count
        trend_data = {}
        for obj in daily_latest:
            date_key = obj.collected_at.strftime("%Y-%m-%d")
            trend_data[date_key] = trend_data.get(date_key, 0) + obj.member_count

        # ✅ مرتب‌سازی بر اساس تاریخ
        sorted_items = sorted(trend_data.items())
        categories = [item[0] for item in sorted_items]
        data = [item[1] for item in sorted_items]

        result = [{"date": date, "total_members": total} for date, total in sorted_items]
        total_members = data[-1] if data else 0

        chart_format = [{
            "categories": categories,
            "data": data,
            "color": "#b2532f"
        }]

        return Response({
            "trend": result,
            "chart": chart_format,
            "total_members": total_members
        })


class UserLastPostsViewSet(viewsets.ViewSet):
    """
    نمایش پست‌های کاربر با تمام فیلترهای ممکن (با پشتیبانی از فرمت comma-separated)
    """

    def list(self, request):
        user = request.user

        # 🔐 بررسی دسترسی کاربر به کانال‌ها
        if not hasattr(user, 'userprofile') or not user.userprofile.channels.exists():
            return Response(
                {"error": "شما به هیچ کانالی دسترسی ندارید."},
                status=status.HTTP_403_FORBIDDEN
            )

        # 🎯 دریافت تمام پارامترهای فیلتر — به صورت comma-separated
        search_query = request.query_params.get('search', None)
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        platform_str = request.query_params.get('platform', '')
        province_str = request.query_params.get('province', '')
        author_str = request.query_params.get('author', '')
        channel_str = request.query_params.get('channel', '')

        # 🧹 تابع کمکی برای تبدیل "1,2,3" به لیست عدد
        def parse_ids(s):
            if not s.strip():
                return []
            try:
                return [int(x.strip()) for x in s.split(',') if x.strip().isdigit()]
            except ValueError:
                return []

        platform_ids = parse_ids(platform_str)
        province_ids = parse_ids(province_str)
        author_ids = parse_ids(author_str)
        channel_ids = parse_ids(channel_str)

        # 🛡️ فیلترهای پایه - فقط کانال‌های مجاز کاربر
        allowed_channels = user.userprofile.channels.only('id')  # فقط آی‌دی لازمه
        allowed_channel_ids = set(allowed_channels.values_list('id', flat=True))

        base_filters = {
            'channel__in': allowed_channels
        }

        # ➕ افزودن فیلترهای اختیاری با __in
        if channel_ids:
            requested_ids = set(channel_ids)
            valid_channel_ids = allowed_channel_ids & requested_ids
            if not valid_channel_ids:
                return Response(
                    {"error": "کانال‌های انتخاب شده یا وجود ندارند یا دسترسی ندارید."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            base_filters['channel__id__in'] = list(valid_channel_ids)

        if author_ids:
            base_filters['author__id__in'] = author_ids

        if platform_ids:
            base_filters['channel__platform__id__in'] = platform_ids

        if province_ids:
            base_filters['channel__province__id__in'] = province_ids

        # 📝 دریافت پست‌ها با فیلترهای پایه
        posts = Post.objects.filter(**base_filters)

        # 🔍 فیلتر جستجو
        if search_query:
            posts = posts.filter(
                Q(post_text__icontains=search_query) |
                Q(hashtags__icontains=search_query) |
                Q(author__name__icontains=search_query) |
                Q(author__family__icontains=search_query) |
                Q(channel__name__icontains=search_query)
            ).distinct()

        # 📅 فیلتر تاریخ
        start_date_parsed = parse_date(start_date) if start_date else None
        end_date_parsed = parse_date(end_date) if end_date else None

        if start_date and end_date:
            if not start_date_parsed or not end_date_parsed:
                return Response(
                    {"error": "فرمت تاریخ نامعتبر است. استفاده از YYYY-MM-DD یا YYYY/MM/DD الزامی است."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            posts = posts.filter(collected_at__range=[start_date_parsed, end_date_parsed])

        # محاسبه آمار
        total_posts = posts.count()
        total_views = posts.aggregate(Sum('views'))['views__sum'] or 0

        # مرتب‌سازی و محدود کردن به 10 پست آخر
        posts = posts.select_related(
            'channel',
            'author',
            'channel__platform',
            'channel__province'
        ).order_by('-collected_at')[:10]

        serializer = PostSerializer(posts, many=True)

        # ✅ خروجی کاملاً مشابه قبل — بدون هیچ تغییری در ساختار
        return Response({
            "total_posts": total_posts,
            "total_views": total_views,
            "filters": {
                "platform": platform_ids[0] if platform_ids else None,
                "province": province_ids[0] if province_ids else None,
                "author": author_ids[0] if author_ids else None,
                "channel": channel_ids[0] if channel_ids else None,
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


class ProvinceListViewSet(viewsets.ViewSet):
    """
    نمایش لیست استان‌هایی که کاربر به کانال‌های آن‌ها دسترسی دارد.
    - ادمین: همه استان‌ها
    - کاربر عادی: فقط استان‌های مرتبط با کانال‌هایش
    """

    def list(self, request):
        user = request.user

        # 🔐 اگر کاربر لاگین نکرده
        if not user.is_authenticated:
            return Response({"error": "لاگین الزامی است."}, status=401)

        # 🟢 ادمین: همه استان‌ها
        if user.is_superuser:
            provinces = Province.objects.all().order_by('name')

        # 🔐 کاربر عادی: فقط استان‌هایی که کانال‌هایش در اون‌ها قرار دارند
        else:
            if not hasattr(user, 'userprofile') or not user.userprofile.channels.exists():
                return Response([], status=200)  # کاربر به کانالی دسترسی نداره

            # گرفتن استان‌های مرتبط با کانال‌های کاربر
            provinces = Province.objects.filter(
                id__in=user.userprofile.channels.values_list('province_id', flat=True)
            ).distinct().order_by('name')

        # ✅ سریالایز و پاسخ
        serializer = ProvinceSerializer(provinces, many=True)
        return Response(serializer.data)


