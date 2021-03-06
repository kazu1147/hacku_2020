# Generated by Django 2.2.3 on 2020-10-12 01:51

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lat', models.FloatField(verbose_name='緯度')),
                ('lon', models.FloatField(verbose_name='経度')),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30, verbose_name='名前')),
            ],
        ),
        migrations.CreateModel(
            name='Form',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=32, verbose_name='タイトル')),
                ('description', models.CharField(blank=True, max_length=80, verbose_name='概要')),
                ('text', models.CharField(blank=True, max_length=255, verbose_name='テキスト')),
                ('image_url', models.CharField(blank=True, max_length=255, null=True, verbose_name='画像パス')),
                ('fab_count', models.FloatField(verbose_name='評価カウント')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='map.Customer', verbose_name='顧客')),
                ('location', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to='map.Location', verbose_name='位置情報')),
                ('tag', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to='map.Tag', verbose_name='タグ')),
            ],
        ),
        migrations.AddField(
            model_name='customer',
            name='location',
            field=models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to='map.Location', verbose_name='位置情報'),
        ),
        migrations.AddField(
            model_name='customer',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='顧客情報'),
        ),
    ]
