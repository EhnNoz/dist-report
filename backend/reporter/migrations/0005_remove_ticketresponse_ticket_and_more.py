# Generated by Django 4.2.21 on 2025-07-08 10:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reporter', '0004_ticket_alter_userprofile_options_ticketresponse'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ticketresponse',
            name='ticket',
        ),
        migrations.RemoveField(
            model_name='ticketresponse',
            name='user',
        ),
        migrations.DeleteModel(
            name='Ticket',
        ),
        migrations.DeleteModel(
            name='TicketResponse',
        ),
    ]
