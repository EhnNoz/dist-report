import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# چرخۀ ارسال تسک در هر دقیقه
from celery.schedules import crontab
app.conf.beat_schedule = {
    'send-scheduled-posts-every-minute': {
        'task': 'sender.tasks.send_scheduled_posts',
        'schedule': crontab(),
    },
}