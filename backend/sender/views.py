from rest_framework import viewsets
from .models import Province, Channel, Post, Category, PlatformToken
from .serializers import ProvinceSerializer, ChannelSerializer, PostSerializer, \
    CategorySerializer, PlatformTokenSerializer, CurrentUserSerializer, UserSerializer
from django.core.exceptions import PermissionDenied
from django_filters import rest_framework as filters
from rest_framework.permissions import IsAuthenticated
from .permissions import IsSuperuser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model


class ChannelFilter(filters.FilterSet):
    channel_id = filters.CharFilter(field_name='channel_id', lookup_expr='exact')
    platform = filters.CharFilter(field_name='platform', lookup_expr='exact')

    class Meta:
        model = Channel
        fields = ['channel_id', 'platform']


class ProvinceViewSet(viewsets.ModelViewSet):
    # queryset = Province.objects.all()
    # serializer_class = ProvinceSerializer
    #
    # def get_permissions(self):
    #     if self.action in ['create', 'update', 'partial_update', 'destroy']:
    #         self.permission_classes = [IsSuperuser]
    #     return super().get_permissions()


    serializer_class = ProvinceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            raise PermissionDenied("شما باید وارد حساب کاربری خود شوید.")

        return Province.objects.filter(channel__users=user).distinct()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        if not queryset.exists():
            return Response(
                {"detail": "هیچ مرکزی ثبت نشده است."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsSuperuser]
        return super().get_permissions()


class CategoryViewSet(viewsets.ModelViewSet):
    # queryset = Category.objects.all()
    # serializer_class = CategorySerializer
    #
    # def get_permissions(self):
    #     if self.action in ['create', 'update', 'partial_update', 'destroy']:
    #         self.permission_classes = [IsSuperuser]
    #     return super().get_permissions()

    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            raise PermissionDenied("شما باید وارد حساب کاربری خود شوید.")

        return Category.objects.filter(channel__users=user).distinct()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        if not queryset.exists():
            return Response(
                {"detail": "هیچ دسته‌بندی ثبت نشده است."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsSuperuser]
        return super().get_permissions()


class PlatformTokenViewSet(viewsets.ModelViewSet):
    queryset = PlatformToken.objects.all()
    serializer_class = PlatformTokenSerializer


class ChannelViewSet(viewsets.ModelViewSet):
    # queryset = Channel.objects.all()
    serializer_class = ChannelSerializer
    permission_classes = [IsAuthenticated]
    # filter_backends = [filters.DjangoFilterBackend]
    # filterset_class = ChannelFilter
    def get_queryset(self):
        user = self.request.user
        queryset = Channel.objects.filter(users=user)

        # گرفتن مقادیر فیلتر از URL
        channel_id = self.request.query_params.get('channel_id', None)
        platform = self.request.query_params.get('platform', None)
        category = self.request.query_params.get('category', None)
        type = self.request.query_params.get('type', None)

        # فقط فیلتر کن اگر مقدار وارد شده باشه
        if channel_id:
            queryset = queryset.filter(channel_id=channel_id)

        if platform:
            queryset = queryset.filter(platform=platform)

        if category:
            queryset = queryset.filter(category=category)

        if type:
            queryset = queryset.filter(type=type)

        return queryset

    def get_permissions(self):
        """
        تعیین مجوز براساس نوع عملیات
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsSuperuser]

        return super().get_permissions()



class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    queryset = Post.objects.all()

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            raise PermissionDenied("شما باید وارد حساب کاربری خود شوید.")

        if not user.is_superuser:
            return self.queryset.filter(created_by=user)

        return self.queryset

    def perform_create(self, serializer):
        # ✅ اینجا created_by خودکار با کاربر لاگین‌کرده ست می‌شه
        serializer.save(created_by=self.request.user)

        # if not self.request.user.is_superuser:
        #     return Post.objects.filter(created_by=self.request.user)
        # return Post.objects.all()


class CurrentUserViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CurrentUserSerializer

    def get_queryset(self):
        # فقط کاربر جاری رو برمی‌گردونیم
        return self.request.user.__class__.objects.filter(id=self.request.user.id)

    def get_object(self):
        # می‌تونیم اینجا هم کاربر جاری رو برگردونیم
        return self.request.user


User = get_user_model()


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()

    def list(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return Response(
                {"detail": "دسترسی غیرمجاز. فقط سوپر ادمین می‌تواند این عمل را انجام دهد."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().list(request, *args, **kwargs)