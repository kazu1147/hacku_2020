from django.contrib.auth.models import User
from django.db import models


# Create your models here.
class Location(models.Model):
    lat = models.FloatField(verbose_name="緯度", null=False, blank=False)
    lon = models.FloatField(verbose_name="経度", null=False, blank=False)
    
    def __str__(self):
        return f"({self.lat},{self.lon})"


class Customer(models.Model):
    user = models.OneToOneField(User, verbose_name="顧客情報", on_delete=models.PROTECT, null=False, blank=False)
    location = models.OneToOneField(Location, verbose_name="位置情報", on_delete=models.PROTECT, null=False, blank=False)

    def __str__(self):
        return f"{self.user}"


class Tag(models.Model):
    name = models.CharField(verbose_name="名前", max_length=30, null=False, blank=False)
    
    def __str__(self):
        return f"{self.name}"


class Form(models.Model):
    customer = models.ForeignKey(Customer, verbose_name="顧客", on_delete=models.CASCADE, null=False, blank=False)
    tag = models.ForeignKey(Tag, verbose_name="タグ", on_delete=models.PROTECT, null=False, blank=False)
    title = models.CharField(verbose_name="タイトル", max_length=32, null=False, blank=False)
    description = models.CharField(verbose_name="概要", max_length=80, null=False, blank=True)
    text = models.CharField(verbose_name="テキスト", max_length=255, null=False, blank=True)
    image_url = models.CharField(verbose_name="画像パス", max_length=255, null=True, blank=True)
    address = models.CharField(verbose_name="住所", max_length=255, null=True, blank=True)
    prefecture = models.CharField(verbose_name="都道府県名", max_length=20, null=True, blank=True)
    location = models.OneToOneField(Location, verbose_name="位置情報", on_delete=models.PROTECT, null=False, blank=False)
    fab_count = models.FloatField(verbose_name="評価カウント", null=False, blank=False)

    def __str__(self):
        return f"{self.title}"
