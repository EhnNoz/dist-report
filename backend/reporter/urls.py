from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DashboardViewSet, PlatformStatsViewSet, ChannelStatsViewSet, ChannelListViewSet, AuthorStatsViewSet,\
    PostViewSet, ChannelMemberViewSet, ReadOnlyAuthorViewSet, ReadOnlyChannelViewSet, ChannelMemberTrendViewSet, \
    UserLastPostsViewSet, AuthorViewSet, ProvinceListViewSet


router = DefaultRouter()
router.register(r'dashboard', DashboardViewSet, basename='dashboard')
router.register(r'platform-stats', PlatformStatsViewSet, basename='platform-stats')
router.register(r'channel-stats', ChannelStatsViewSet, basename='channel-stats')
router.register(r'channels', ChannelListViewSet, basename='channel-list')
router.register(r'author-stats', AuthorStatsViewSet, basename='author-stats')
router.register(r'posts', PostViewSet, basename='posts')
router.register(r'channel-members', ChannelMemberViewSet, basename='channel-members')
router.register(r'authors', ReadOnlyAuthorViewSet, basename='author')
router.register(r'channel-code', ReadOnlyChannelViewSet, basename='channel-code')
router.register(r'member-trend', ChannelMemberTrendViewSet, basename='member-trend')
router.register(r'user-posts', UserLastPostsViewSet, basename='user-posts')
router.register(r'authors-update', AuthorViewSet, basename='authors-update')
router.register(r'dashboard-provinces', ProvinceListViewSet, basename='dashboard-provinces')


urlpatterns = [
    path('', include(router.urls)),
]