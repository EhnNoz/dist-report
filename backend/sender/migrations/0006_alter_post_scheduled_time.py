# Generated by Django 4.2.21 on 2025-05-22 07:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sender', '0005_alter_channel_options_alter_post_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='scheduled_time',
            field=models.DateTimeField(),
        ),
    ]
