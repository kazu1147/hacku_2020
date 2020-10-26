import datetime
import json

import pandas as pd
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

# Create your views here.
from django.utils import timezone
from django.utils.timezone import localtime, make_aware

import constants
from map.models import Form, Covid_level


# トップページにリダイレクトする関数
@login_required
def redirect_top(request):
    return redirect('map:top')


# トップページを表示する関数
@login_required
def show_top(request):
    # 全てのスポットを取得
    spots = Form.objects.all().values('id', 'title', 'tag__name', 'description', 'image_url', 'fab_count',
                                      'location__lon', 'location__lat')
    print(spots)
    # [{'id': 1, 'title': '町はずれにあるおしゃれなレストラン', 'tag__name': 'カフェ', 'description': '300円でコーヒーとお手製サンドイッチが楽しめます', 'image_url': None, '
    # fab_count': 4.0, 'location__lon': 217.221, 'location__lat': 122.222}, {'id': 2, 'title': '町の公民館でコロナを回避！', 'tag__name': '安全', 'description': '緊急時には150人の収容
    # が可能です', 'image_url': None, 'fab_count': 12.0, 'location__lon': 219.871, 'location__lat': 123.211}]
    # valuesにより、上記のような辞書型{}の配列[]を作っている

    # 各エリアの危険度を取得
    # 時間(何月何日何時の定期実行かを把握->awareで！) -> 2020/10/27 14:00 -> 2020/10/27 00:00
    today = get_today_aware_obj()
    covid_area_levels = Covid_level.objects.filter(pk__gte=today).order_by('-pk')

    # 該当したモデルから最新のものを取得する
    if len(covid_area_levels) != 0:
        # 辞書型に変換
        covid_area_levels = mapping_area_color(covid_area_levels[0])
    print(covid_area_levels)
    contexts = {
        "spots": spots,
        "covid_area_levels": json.dumps(covid_area_levels),
    }

    return render(request, 'map/top.html', contexts)


# スポットの入力画面を表示する関数
@login_required
def show_form(request):
    return render(request, 'map/form.html')


# スポットの評価を1増やす関数
@login_required
def plus_fab(request, id):
    try:
        target_form = get_object_or_404(Form, id=id)
        target_form.fab_count += 1
        target_form.save()
        return JsonResponse({"status": "success"})
    except Http404:
        return JsonResponse({"status": "fail"})
    except Exception:
        return JsonResponse({"status": "fail"})


# 今日の日付をtimezoneを考慮して返す
def get_today_aware_obj() -> datetime:
    now = localtime(timezone.now())
    # nativeで比較させる
    dt_native = datetime.datetime(now.year, now.month, now.day, 0, 0, 0, 0)
    dt_aware = make_aware(dt_native)
    return dt_aware


# 色をマッピングして返す
def mapping_area_color(covid_level_obj: Covid_level):
    df = pd.read_csv('city_area_map.csv', engine='python', encoding='cp932')
    mapping_dict = {}
    for i, area in enumerate(constants.AREAS):
        level = getattr(covid_level_obj, area)
        mapping_dict[i+1] = constants.COVID_AREA_COLORS.get(level)
    df_db = pd.DataFrame(list(mapping_dict.items()),columns=['area_number', 'color'])
    df = pd.merge(df, df_db)
    df.drop('area_number', axis=1, inplace=True)
    return df.to_dict(orient='records')
