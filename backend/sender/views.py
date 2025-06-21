from rest_framework import viewsets
from .models import Province, Channel, Post, Category, PlatformToken
from .serializers import ProvinceSerializer, ChannelSerializer, PostSerializer, \
    CategorySerializer, PlatformTokenSerializer
from django.core.exceptions import PermissionDenied
from django_filters import rest_framework as filters


class ChannelFilter(filters.FilterSet):
    channel_id = filters.CharFilter(field_name='channel_id', lookup_expr='exact')
    platform = filters.CharFilter(field_name='platform', lookup_expr='exact')

    class Meta:
        model = Channel
        fields = ['channel_id', 'platform']


class ProvinceViewSet(viewsets.ModelViewSet):
    queryset = Province.objects.all()
    serializer_class = ProvinceSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class PlatformTokenViewSet(viewsets.ModelViewSet):
    queryset = PlatformToken.objects.all()
    serializer_class = PlatformTokenSerializer


class ChannelViewSet(viewsets.ModelViewSet):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = ChannelFilter


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            raise PermissionDenied("شما باید وارد حساب کاربری خود شوید.")

        if not user.is_superuser:
            return Post.objects.filter(created_by=user)

        return Post.objects.all()

        # if not self.request.user.is_superuser:
        #     return Post.objects.filter(created_by=self.request.user)
        # return Post.objects.all()