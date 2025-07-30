from django.test import TestCase

# Create your tests here.
import requests

apiToken = "https://api.telegram.org/bot7857598579:AAG7KLCXqUXY6hb6qZwx3UNkib2iTsxhLtU/sendMessage"
chat_id = "-1002250661524"
message = "Hello, this is a test message!"

# apiURL = f'https://api.telegram.org/bot{apiToken}/sendMessage'

# تنظیم پروکسی SOCKS (مثال برای SOCKS5)
proxies = {
    'http': 'socks5://test:test2915@37.156.146.155:9443',
    'https': 'socks5://test:test2915@37.156.146.155:9443'
}

# ارسال درخواست با پروکسی
response = requests.post(apiToken, json={'chat_id': chat_id, 'text': message})

print(response.status_code)
print(response.text)


# import asyncio
# from telegram import Bot
# from telegram.request import HTTPXRequest
#
#
# async def send_message_with_proxy():
#     proxy_url = "socks5://test:test2915@37.156.146.155:9443"  # پروکسی شما
#     request = HTTPXRequest(proxy=proxy_url)
#     bot = Bot(token="7857598579:AAG7KLCXqUXY6hb6qZwx3UNkib2iTsxhLtU", request=request)
#     await bot.send_message(chat_id="-1002250661524", text="Hello via Proxy!")
#
# asyncio.run(send_message_with_proxy())
