

**This is a Tutorial Project for Content Management**

Python 3.8+
Django 4.x
Redis Server

chbackend/
├── config/           
├── sender/          
│   ├── models.py     
│   ├── tasks.py     
│   ├── admin.py     
│   └── ...
├── manage.py
└── requirements.txt 

git clone

pip install -r requirements.txt

python manage.py migrate

python manage.py createsuperuser

redis-server

celery -A config worker --loglevel=info -P eventlet -c 3

celery -A config beat --loglevel=info --max-interval=1

python manage.py collectstatic

python manage.py runserver







