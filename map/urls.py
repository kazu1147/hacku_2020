from django.urls import path, include

from .views import *

app_name = "map"

urlpatterns = [
    # 地図一覧・検索(topページ)
    path('top/', show_top, name="top"),
    path('form/', show_form, name="form"),
    path('', redirect_top, name="redirect_top"),

    # 非同期処理用
    path('api/form/<int:id>/', plus_fab, name="plus_fab"),

]