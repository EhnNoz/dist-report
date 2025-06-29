# Generated by Django 4.2.21 on 2025-05-31 12:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sender', '0014_dashboardchannel_platformpost_channelstats'),
    ]

    operations = [
        migrations.CreateModel(
            name='Platform',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('icon', models.CharField(blank=True, max_length=255, null=True)),
            ],
        ),
        migrations.AlterModelOptions(
            name='channelstats',
            options={'ordering': ['-collected_at'], 'verbose_name': 'داشبورد - اعضای  کانال', 'verbose_name_plural': 'داشبورد - اعضای کانال\u200cها'},
        ),
        migrations.AlterModelOptions(
            name='dashboardchannel',
            options={'verbose_name': 'داشبورد - کانال ها', 'verbose_name_plural': 'داشبورد - کانال ها'},
        ),
        migrations.AlterModelOptions(
            name='platformpost',
            options={'verbose_name': 'داشبورد - پست های جمع آوری شده', 'verbose_name_plural': 'داشبورد - پست های جمع آوری شده'},
        ),
        migrations.AlterField(
            model_name='channel',
            name='platform',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='sender.platform'),
        ),
        migrations.AlterField(
            model_name='dashboardchannel',
            name='platform',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='sender.platform'),
        ),
        migrations.AlterField(
            model_name='platformtoken',
            name='platform',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='sender.platform', verbose_name='پلتفرم'),
        ),
    ]
