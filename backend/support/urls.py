from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TicketViewSet, AdminTicketViewSet, NotificationViewSet, UserNotificationViewSet, \
    AllUsersViewSet\
    # , GeneralNoticeViewSet

router = DefaultRouter()
router.register(r'tickets', TicketViewSet, basename='ticket')
router.register(r'admin-tickets', AdminTicketViewSet, basename='admin-ticket')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'user-notifications', UserNotificationViewSet, basename='user-notification')
router.register(r'users', AllUsersViewSet, basename='user')
# router.register(r'notices', GeneralNoticeViewSet, basename='notice')



urlpatterns = [
    path('', include(router.urls)),
]