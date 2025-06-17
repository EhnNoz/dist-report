from celery import shared_task
from .models import Post, PlatformToken
import requests
import os
from django.conf import settings
from datetime import datetime
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def send_scheduled_post(post_id):
    try:
        tokens = {
            token.platform: token.token
            for token in PlatformToken.objects.filter(is_active=True)
        }

        post = Post.objects.get(id=post_id)

        # $#############################
        # if post.image:
        #     image_path = os.path.join(settings.MEDIA_ROOT, str(post.image))
        #     flag = 'picture'
        # else:
        #     flag = 'text'
        image_path = os.path.join(settings.MEDIA_ROOT, str(post.media)) if post.media else None
        if post.media:
            file_ext = os.path.splitext(str(post.media))[1].lower()
            with open(image_path, 'rb') as media_file:

                if file_ext in ['.jpg', '.jpeg', '.png', '.gif']:
                    insert_media = 'picture'

                elif file_ext in ['.mp4', '.mkv', '.mov', '.avi']:
                    insert_media = 'video'

                else:
                    raise Exception(f"فرمت فایل ({file_ext}) پشتیبانی نمی‌شود.")
        else:
            insert_media = 'text'




        # print("*************")
        # if not os.path.exists(image_path):
        #     raise FileNotFoundError(f"Image file not found: {image_path}")
        # print("*************")

        for channel in post.channels.all():
            chat_id = channel.channel_id  # مثلاً "@my_channel" یا "-1001234567890"
            print(chat_id)
            print("*************")
            titr = post.titr
            caption = post.caption
            author = post.author
            hashtags = post.hashtags

            message = ""
            if titr:
                message += f"{titr}\n\n"
            if caption:
                message += f"{caption}\n\n"
            if hashtags:
                message += f"{hashtags}\n\n"
            if author:
                message += f"<<{author}>>"

            platform = channel.platform
            apiToken = tokens.get(platform)

            if platform == 'telegram':
                if insert_media == 'picture':
                    apiURL = f'https://api.telegram.org/bot{apiToken}/sendDocument'
                    response = requests.post(apiURL, data={'chat_id': chat_id, 'caption': message},
                                             files={'document': open(image_path, 'rb')})
                elif insert_media == 'video':
                    apiURL = f'https://api.telegram.org/bot{apiToken}/sendDocument'
                    response = requests.post(apiURL, data={'chat_id': chat_id, 'caption': message},
                                             files={'document': open(image_path, 'rb')})
                else:
                    apiURL = f'https://api.telegram.org/bot{apiToken}/sendMessage'
                    response = requests.post(apiURL, json={'chat_id': chat_id, 'text': message})

            elif platform == 'bale':
                if insert_media == 'picture':
                    apiURL = f'https://tapi.bale.ai/bot{apiToken}/SendPhoto'
                    response = requests.post(apiURL, data={'chat_id': chat_id, 'caption': message},
                                             files={'photo': open(image_path, 'rb')})
                elif insert_media == 'video':
                    apiURL = f'https://tapi.bale.ai/bot{apiToken}/SendVideo'
                    response = requests.post(apiURL, data={'chat_id': chat_id, 'caption': message},
                                             files={'video': open(image_path, 'rb')})
                else:
                    apiURL = f'https://tapi.bale.ai/bot{apiToken}/sendMessage'
                    response = requests.post(apiURL, json={'chat_id': chat_id, 'text': message})

            elif platform == 'eitaa':
                if insert_media == 'picture':
                    apiURL = f'https://eitaayar.ir/api/{apiToken}/sendFile'
                    response = requests.post(apiURL, data={'chat_id': chat_id, 'caption': message},
                                             files={'file': open(image_path, 'rb')})
                elif insert_media == 'video':
                    apiURL = f'https://eitaayar.ir/api/{apiToken}/sendFile'
                    response = requests.post(apiURL, data={'chat_id': chat_id, 'caption': message},
                                             files={'file': open(image_path, 'rb')})
                else:
                    apiURL = f'https://eitaayar.ir/api/{apiToken}/sendMessage'
                    response = requests.post(apiURL, json={'chat_id': chat_id, 'text': message})

            else:
                raise Exception(f"پلتفرم {platform} پشتیبانی نمی‌شود")

            # if platform == 'bale':
            #     response = requests.post(apiURL, data={'chat_id': chat_id, 'caption': caption},
            #                         files={'photo': open(image_path, 'rb')})
            # elif platform == 'eitaa':
            #     print("*************")

            # بررسی موفقیت ارسال
            if response.status_code != 200:
                raise Exception(f"Failed to send to {chat_id}: {response.text}")

        try:
            os.remove(image_path)
        except Exception as e:
            print(e)
            pass
        post.delete()

        ################################

        # ارسال عکس و کپشن از طریق API تلگرام
        # url = f"https://api.telegram.org/bot {settings.TELEGRAM_BOT_TOKEN}/sendPhoto"
        # url = f'https://tapi.bale.ai/bot{apiToken}/sendMessage'

        # with open(os.path.join(settings.MEDIA_ROOT, str(post.image)), 'rb') as image_file:
        #     files = {'photo': image_file}
        #
        #     data = {'chat_id': post.channels.first().channel_id, 'caption': post.caption}
        #     response = requests.post(url, data=data, post.caption)
        #
        # if response.status_code == 200:
        #     post.sent = True
        #     post.save()
        # else:
        #     print("Failed to send via Telegram API")

    except Exception as e:
        # print("not allowed")
        print(f"Error: {str(e)}")
        post.sent = False
        post.save()


@shared_task
def check_scheduled_posts():
    now = timezone.now()
    posts = Post.objects.filter(scheduled_time__lte=now, sent=False)
    for post in posts:
        send_scheduled_post.delay(post.id)