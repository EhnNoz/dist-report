from collections import Counter
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q, Sum, Count, OuterRef, Subquery
from datetime import datetime
from .models import *
from .serializers import *
#from .permissions import IsAdminOrOwnProvince
# from rest_framework.filters import SearchFilter


def parse_date(date_str):
    """تبدیل تاریخ با فرمت‌های مختلف به date object"""
    for fmt in ('%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y'):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


class DashboardViewSet(viewsets.ViewSet):
    # permission_classes = [IsAdminOrOwnProvince]
    # filter_backends = [SearchFilter]
    # search_fields = ['name', 'family', 'national_code', 'email', 'expertise']

    def list(self, request):
        print('****************')

        search_query = request.query_params.get('search', None)
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        platform_id = request.query_params.get('platform')
        province_id = request.query_params.get('province')
        author_id = request.query_params.get('author')
        channel_id = request.query_params.get('channel')


        # user_province = getattr(request.user, 'province', None)
        filters = {}

        # if not request.user.is_superuser:
        #     filters['province_id'] = user_province.id if user_province else None
        #
        # if province_id and request.user.is_superuser:
        #     filters['province_id'] = province_id
        #
        if province_id:
            filters['province_id'] = province_id

        if platform_id:
            filters['platform_id'] = platform_id

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

        # if start_date and end_date:
        #     try:
        #         start_date_parsed = datetime.strptime(start_date, "%Y-%m-%d").date()
        #         end_date_parsed = datetime.strptime(end_date, "%Y-%m-%d").date()
        #         posts = posts.filter(collected_at__range=[start_date_parsed, end_date_parsed])
        #     except ValueError:
        #         return Response({"error": "فرمت تاریخ نامعتبر است."}, status=400)

        start_date_parsed = parse_date(start_date) if start_date else None
        end_date_parsed = parse_date(end_date) if end_date else None

        if start_date and end_date:
            if not start_date_parsed or not end_date_parsed:
                return Response(
                    {"error": "فرمت تاریخ نامعتبر است. استفاده از YYYY-MM-DD یا YYYY/MM/DD الزامی است."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            posts = posts.filter(collected_at__range=[start_date_parsed, end_date_parsed])

        if author_id:
            posts = posts.filter(author_id=author_id)  # ✅ فیلتر posts بر اساس author_id
            channels = channels.filter(posts__author_id=author_id).distinct()  # ✅ فیلتر کانال‌ها


        # تعداد کل پست‌ها
        total_posts = posts.count()

        # تعداد کل کانال‌ها
        total_channels = channels.count()

        # تعداد کل بازدیدها
        total_views = posts.aggregate(Sum('views'))['views__sum'] or 0



        # total_author = author.count()

        # روند انتشار
        trend = posts.values('collected_at').annotate(count=Count('id'))
        # ⬇️ تبدیل trend به daily_trend با فرمت جدید
        if trend:
            categories = [item['collected_at'].strftime("%Y-%m-%d") for item in trend]
            data = [item['count'] for item in trend]
        else:
            categories = []
            data = []

        daily_trend = [{
            "categories": categories,
            "data": data
        }]

        COLORS = [
            "#347928", "#C0EBA6", "#FFFBE6", "#FCCD2A", "#38C172",
            "#50C878", "#69B076", "#77DD77", "#88C999", "#A8D8B9"
        ]
        # کانال‌های برتر برحسب پست
        top_channels_by_post = channels.annotate(post_count=Count('posts')).order_by('-post_count')[:10]
        # top_channels_by_post = TopChannelSerializer(top_channels_by_post, many=True).data
        # print(top_channels_by_post)

        channel_categories = [channel.name for channel in top_channels_by_post]
        channel_data = [channel.post_count for channel in top_channels_by_post]

        series = []
        for idx, value in enumerate(channel_data):
            color_index = idx % len(COLORS)  # دوری در رنگ‌ها
            series.append({
                "y": value,
                "color": COLORS[color_index]
            })

        top_channels_by_post = [{
            "categories": channel_categories,
            # "data": channel_data,
            "data": series
        }]

        # کانال‌های برتر برحسب بازدید
        top_channels_by_view = channels.annotate(total_views=Sum('posts__views')).order_by('-total_views')[:10]


        channel_categories = [channel.name for channel in top_channels_by_view]
        channel_data = [channel.total_views for channel in top_channels_by_view]



        #########################
        series = []
        for idx, value in enumerate(channel_data):
            color_index = idx % len(COLORS)  # دوری در رنگ‌ها
            series.append({
                "y": value,
                "color": COLORS[color_index]
            })

        top_channels_by_view = [{
            "categories": channel_categories,
            # "data": channel_data,
            "data": series
        }]
        ######################
        # 👤 نویسندگان - تعداد پست

        author_ids = posts.values_list('author', flat=True).distinct()
        authors = Author.objects.filter(id__in=author_ids)
        total_authors = authors.count()
        top_authors_by_post = authors.annotate(count=Count('post')).order_by('-count')[:10]

        series = []
        authors_data = [a.count for a in top_authors_by_post]
        for idx, value in enumerate(authors_data):
            color_index = idx % len(COLORS)  # دوری در رنگ‌ها
            series.append({
                "y": value,
                "color": COLORS[color_index]
            })

        top_authors_by_post = [{
            "categories": [a.name for a in top_authors_by_post],
            # "data": [a.count for a in top_authors_by_post],
            "data": series
        }]

        # 👤 نویسندگان - مجموع بازدید
        author_views = {}
        for post in posts:
            if post.author_id:
                author_views[post.author_id] = author_views.get(post.author_id, 0) + post.views
        author_objects = {a.id: a for a in authors}
        sorted_author_views = sorted(
            [(a_id, author_objects[a_id].name, views) for a_id, views in author_views.items()],
            key=lambda x: x[2],
            reverse=True
        )[:5]
        top_authors_by_view = [{"name": name, "total_views": views} for _, name, views in sorted_author_views]

        series = []
        authors_data = [item["total_views"] for item in top_authors_by_view]
        for idx, value in enumerate(authors_data):
            color_index = idx % len(COLORS)  # دوری در رنگ‌ها
            series.append({
                "y": value,
                "color": COLORS[color_index]
            })

        top_authors_by_view = [{
            "categories": [item["name"] for item in top_authors_by_view],
            # "data": [item["total_views"] for item in top_authors_by_view],
            "data": series
        }]

        # 🔤 کلمات - فقط بر اساس انتشار
        word_list = []
        for p in posts:
            word_list.extend(p.post_text.split())
        word_freq = Counter(word_list).most_common(10)
        top_words_by_post = [{"name": w[0], "weight": w[1]} for w in word_freq]

        # #️⃣ هشتگ‌ها - فقط بر اساس انتشار
        hashtag_list = []
        for p in posts:
            hashtag_list.extend(p.hashtags.split())
        hashtag_freq = Counter(hashtag_list).most_common(10)
        top_hashtags_by_post = [{"name": h[0], "weight": h[1]} for h in hashtag_freq]

        # روند بازدید
        view_trend = posts.values('collected_at').annotate(total_views=Sum('views'))

        # ⬇️ تبدیل trend به daily_trend با فرمت جدید
        if view_trend:
            categories = [item['collected_at'].strftime("%Y-%m-%d") for item in view_trend]
            data = [item['total_views'] for item in view_trend]
        else:
            categories = []
            data = []

        daily_view_trend = [{
            "categories": categories,
            "data": data
        }]

        # 🔢 تعداد پست‌ها بر اساس پلتفرم
        platform_post_counts = (
            Channel.objects.filter(**filters)
            .values('platform__name')
            .annotate(count=Count('posts'))
            .order_by('-count')
        )
        platform_post_counts_list = [
            {"name": item['platform__name'], "y": item['count']} for item in platform_post_counts
        ]

        # 👁️ مجموع بازدیدها بر اساس پلتفرم
        platform_total_views = (
            Channel.objects.filter(**filters)
            .values('platform__name')
            .annotate(total_views=Sum('posts__views'))
            .order_by('-total_views')
        )
        platform_total_views_list = [
            {"name": item['platform__name'], "y": item['total_views'] or 0} for item in platform_total_views
        ]

        return Response({
            "total_posts": total_posts,
            "total_channels": total_channels,
            "total_views": total_views,
            "total_authors":total_authors,
            "daily_trend": daily_trend,
            "top_channels_by_post": top_channels_by_post,
            # "top_channels_by_view": TopChannelSerializer(top_channels_by_view, many=True).data,
            "top_channels_by_view": top_channels_by_view,
            # "top_authors_by_post": [{"name": a.name, "count": a.count} for a in top_authors_by_post],
            "top_authors_by_post": top_authors_by_post,
            "top_authors_by_view": top_authors_by_view,
            "top_hashtags_by_post": top_hashtags_by_post,
            # "top_hashtags_by_view": [h[0] for h in top_hashtags_by_view],
            "top_words_by_post": top_words_by_post,
            # "top_words_by_view": [w[0] for w in top_words_by_view],
            "daily_view_trend": daily_view_trend,
            "platform_post_counts": platform_post_counts_list,
            "platform_total_views": platform_total_views_list
        })


class PlatformStatsViewSet(viewsets.ViewSet):
    # permission_classes = [IsAdminOrOwnProvince]

    def list(self, request):
        search_query = request.query_params.get('search', None)
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        province_id = request.query_params.get('province')
        author_id = request.query_params.get('author')
        channel_id = request.query_params.get('channel')

        # user_province = getattr(request.user, 'province', None)
        filters = {}

        # if not request.user.is_superuser:
        #     if user_province:
        #         filters['province_id'] = user_province.id
        # elif province_id:
        #     filters['province_id'] = province_id

        if province_id:
            filters['province_id'] = province_id

        # post_filters = {}

        if author_id:
            filters['posts__author_id'] = author_id

        if channel_id:
            filters['id'] = channel_id

        platforms = Platform.objects.all()
        result = []

        for platform in platforms:
            channels = Channel.objects.filter(platform=platform, **filters)
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

            # if start_date and end_date:
            #     try:
            #         start_date_parsed = datetime.strptime(start_date, "%Y-%m-%d").date()
            #         end_date_parsed = datetime.strptime(end_date, "%Y-%m-%d").date()
            #         posts = posts.filter(collected_at__range=[start_date_parsed, end_date_parsed])
            #     except ValueError:
            #         return Response(
            #             {"error": "فرمت تاریخ نامعتبر است. استفاده از YYYY-MM-DD الزامی است."},
            #             status=status.HTTP_400_BAD_REQUEST
            #         )

            total_posts = posts.count()
            total_views = posts.aggregate(Sum('views'))['views__sum'] or 0

            logo_url = request.build_absolute_uri(platform.logo.url) if platform.logo else None
            # print(platform.id)
            # print(platform.name)

            result.append({
                "platform_id": platform.id,
                "platform_name": platform.name,
                "platform_logo": logo_url,
                "total_posts": total_posts,
                "total_views": total_views
            })

        serializer = PlatformStatsSerializer(result, many=True)
        return Response(serializer.data)


class ChannelStatsViewSet(viewsets.ViewSet):
    # permission_classes = [IsAdminOrOwnProvince]

    def list(self, request):
        search_query = request.query_params.get('search', None)
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        platform_id = request.query_params.get('platform')
        province_id = request.query_params.get('province')
        author_id = request.query_params.get('author')
        channel_id = request.query_params.get('channel')

        user_province = getattr(request.user, 'province', None)
        filters = {}

        if not request.user.is_superuser:
            if user_province:
                filters['province_id'] = user_province.id
        elif province_id:
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
            # if start_date and end_date:
            #     try:
            #         start_date_parsed = datetime.strptime(start_date, "%Y/%m/%d").date()
            #         end_date_parsed = datetime.strptime(end_date, "%Y/%m/%d").date()
            #         posts = posts.filter(collected_at__range=[start_date_parsed, end_date_parsed])
            #     except ValueError:
            #         return Response(
            #             {"error": "فرمت تاریخ نامعتبر است. استفاده از YYYY-MM-DD الزامی است."},
            #             status=status.HTTP_400_BAD_REQUEST
            #         )

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

        serializer = ChannelStatsSerializer(result, many=True)
        return Response(serializer.data)


class ChannelListViewSet(viewsets.ViewSet):
    # permission_classes = [IsAdminOrOwnProvince]

    def list(self, request):
        # search_query = request.query_params.get('search', None)
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        platform_id = request.query_params.get('platform')
        province_id = request.query_params.get('province')
        author_id = request.query_params.get('author')
        channel_id = request.query_params.get('channel')

        user_province = getattr(request.user, 'province', None)
        filters = {}

        if not request.user.is_superuser:
            if user_province:
                filters['province_id'] = user_province.id
        elif province_id:
            filters['province_id'] = province_id

        if platform_id:
            filters['platform_id'] = platform_id

        if author_id:
            filters['posts__author_id'] = author_id

        if channel_id:
            filters['id'] = channel_id

        channels = Channel.objects.filter(**filters).prefetch_related(
            'members', 'posts'
        )

        # فیلتر بر اساس بازه زمانی (در صورت وجود)
        # if start_date and end_date:
        #     try:
        #         start_date_parsed = datetime.strptime(start_date, "%Y-%m-%d").date()
        #         end_date_parsed = datetime.strptime(end_date, "%Y-%m-%d").date()
        #         channels = channels.filter(posts__collected_at__range=[start_date_parsed, end_date_parsed])
        #     except ValueError:
        #         return Response(
        #             {"error": "فرمت تاریخ نامعتبر است. استفاده از YYYY-MM-DD الزامی است."},
        #             status=400
        #         )

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
            # posts = channels.filter(collected_at__range=[start_date_parsed, end_date_parsed])

        serializer = ChannelDetailSerializer(channels.distinct(), many=True)
        return Response(serializer.data)


class AuthorStatsViewSet(viewsets.ViewSet):
    # permission_classes = [IsAdminOrOwnProvince]

    def list(self, request):
        search_query = request.query_params.get('search', None)
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        platform_id = request.query_params.get('platform')
        province_id = request.query_params.get('province')
        channel_id = request.query_params.get('channel')

        user_province = getattr(request.user, 'province', None)
        filters = {}

        # فیلتر استان
        if not request.user.is_superuser:
            if user_province:
                filters['channel__province_id'] = user_province.id
        elif province_id:
            filters['channel__province_id'] = province_id

        # فیلتر پلتفرم
        if platform_id:
            filters['channel__platform_id'] = platform_id

        if channel_id:
            filters['id'] = channel_id

        # فیلتر تاریخ
        posts = Post.objects.filter(**filters)

        if search_query:
            posts = posts.filter(
                Q(post_text__icontains=search_query) |
                Q(author__name__icontains=search_query) |
                Q(author__family__icontains=search_query) |
                Q(channel__name__icontains=search_query)
            ).distinct()
        # if start_date and end_date:
        #     try:
        #         start_date_parsed = datetime.strptime(start_date, "%Y-%m-%d").date()
        #         end_date_parsed = datetime.strptime(end_date, "%Y-%m-%d").date()
        #         posts = posts.filter(collected_at__range=[start_date_parsed, end_date_parsed])
        #     except ValueError:
        #         return Response(
        #             {"error": "فرمت تاریخ نامعتبر است. استفاده از YYYY-MM-DD الزامی است."},
        #             status=status.HTTP_400_BAD_REQUEST
        #         )
        start_date_parsed = parse_date(start_date) if start_date else None
        end_date_parsed = parse_date(end_date) if end_date else None

        if start_date and end_date:
            if not start_date_parsed or not end_date_parsed:
                return Response(
                    {"error": "فرمت تاریخ نامعتبر است. استفاده از YYYY-MM-DD یا YYYY/MM/DD الزامی است."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            posts = posts.filter(collected_at__range=[start_date_parsed, end_date_parsed])

        # گروه‌بندی نویسندگان بر اساس id و محاسبه آمار
        author_ids = posts.values_list('author', flat=True).distinct()
        authors = Author.objects.filter(id__in=author_ids)

        result = []
        for author in authors:
            author_posts = posts.filter(author=author)
            total_posts = author_posts.count()
            total_views = author_posts.aggregate(total_views=Sum('views'))['total_views'] or 0
            picture_url = author.profile_picture.url if author.profile_picture else None

            result.append({
                "author_id": author.id,
                "author_name": author.full_name,
                "author_picture": request.build_absolute_uri(picture_url) if picture_url else None,
                "total_posts": total_posts,
                "total_views": total_views
            })

        # مرتب‌سازی بر اساس تعداد پست
        result = sorted(result, key=lambda x: x['total_posts'], reverse=True)

        return Response(result)


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer


class ChannelMemberViewSet(viewsets.ModelViewSet):
    queryset = ChannelMember.objects.all()
    serializer_class = ChannelMemberSerializer


class ReadOnlyAuthorViewSet(viewsets.ViewSet):
    # permission_classes = [IsAuthenticated]  # فقط کاربران لاگین‌کرده
    serializer_class = AuthorSerializer

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
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        platform_id = request.query_params.get('platform')
        province_id = request.query_params.get('province')
        channel_id = request.query_params.get('channel')  # ✅ فیلتر کانال

        filters = {}

        # ✅ فیلترهای استان، پلتفرم، کانال
        if province_id:
            filters['province_id'] = province_id
        if platform_id:
            filters['platform_id'] = platform_id
        if channel_id:
            filters['id'] = channel_id  # فقط یک کانال خاص

        # ✅ گرفتن کانال‌های فیلتر شده
        channels = Channel.objects.filter(**filters).distinct()

        # ✅ گرفتن پست‌ها و عضویت‌ها با فیلتر کانال
        members = ChannelMember.objects.filter(channel__in=Subquery(channels.values('id')))

        # # ✅ فیلتر تاریخ
        # if start_date and end_date:
        #     try:
        #         start_date_parsed = datetime.strptime(start_date, "%Y-%m-%d").date()
        #         end_date_parsed = datetime.strptime(end_date, "%Y-%m-%d").date()
        #         members = members.filter(collected_at__range=[start_date_parsed, end_date_parsed])
        #     except ValueError:
        #         return Response(
        #             {"error": "فرمت تاریخ نامعتبر است. استفاده از YYYY-MM-DD الزامی است."},
        #             status=status.HTTP_400_BAD_REQUEST
        #         )

        start_date_parsed = parse_date(start_date) if start_date else None
        end_date_parsed = parse_date(end_date) if end_date else None

        if start_date and end_date:
            if not start_date_parsed or not end_date_parsed:
                return Response(
                    {"error": "فرمت تاریخ نامعتبر است. استفاده از YYYY-MM-DD یا YYYY/MM/DD الزامی است."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            posts = members.filter(collected_at__range=[start_date_parsed, end_date_parsed])

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

        return Response({
            "trend": result,
            "chart": chart_format
        })

