import configparser
import datetime
import json
import os
import random
import re
import uuid

import pandas as pd
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

# Create your views here.
from django.utils import timezone
from django.utils.timezone import localtime, make_aware

import constants
from map.models import Form, Covid_level, Tag, Location, Customer

import googlemaps

from project.settings import BASE_DIR

conf = configparser.ConfigParser()
settingsFilePath = os.path.join(BASE_DIR, "settings.ini")
conf.read_file(open(settingsFilePath, "r"))
googleapikey = conf['googlemap']['key']
gmaps = googlemaps.Client(key=googleapikey)

# トップページにリダイレクトする関数
@login_required
def redirect_top(request):
    return redirect('map:top')


# トップページを表示する関数
@login_required
def show_top(request):
    # 各エリアの危険度を取得
    # 時間(何月何日何時の定期実行かを把握->awareで！) -> 2020/10/27 14:00 -> 2020/10/27 00:00
    today = get_today_aware_obj()
    covid_area_levels = Covid_level.objects.filter(pk__gte=today).order_by('-pk')

    # 該当したモデルから最新のものを取得する
    if len(covid_area_levels) != 0:
        # 辞書型に変換
        covid_area_levels = mapping_area_color(covid_area_levels[0])
    else:
        covid_area_levels = None

    if request.method == "GET":
        # 全てのスポットを取得
        spots = Form.objects.all().order_by('id')\
            .values('id', 'title', 'tag__name', 'description', 'image_url', 'fab_count', 'location__lon', 'location__lat')
        spots = list(map(none_to_str, spots))
        print(spots)
        #print(gmaps.geolocate())
        # [{'id': 1, 'title': '町はずれにあるおしゃれなレストラン', 'tag__name': 'カフェ', 'description': '300円でコーヒーとお手製サンドイッチが楽しめます', 'image_url': None, '
        # fab_count': 4.0, 'location__lon': 217.221, 'location__lat': 122.222}, {'id': 2, 'title': '町の公民館でコロナを回避！', 'tag__name': '安全', 'description': '緊急時には150人の収容
        # が可能です', 'image_url': None, 'fab_count': 12.0, 'location__lon': 219.871, 'location__lat': 123.211}]
        # valuesにより、上記のような辞書型{}の配列[]を作っている

        contexts = {
            "spots": spots,
            "covid_area_levels": json.dumps(covid_area_levels),
        }

    else:
        contexts = None
        # データ(検索条件)を受け取る
        print(request.POST)
        # 受け取った検索条件で検索をかける

        # 検索に引っかかったスポットをフロント側に渡す
        pass

    return render(request, 'map/top.html', contexts)

# スポットの入力画面を表示する関数
@login_required
def show_form(request):
    if request.method == "GET":
        tags = Tag.objects.all().order_by('id')
        contexts = {
            'file_uuid': str(uuid.uuid4()),
            'search_tags': tags,
        }
        return render(request, 'map/form_html.html', contexts)
    elif request.method == "POST":
        print(request.POST)
        # データの受け取り
        title = request.POST.get('input_title', None)
        description = request.POST.get('input_description', None)
        tag_id = request.POST.get('input_tag', None)
        address = request.POST.get('input_address', None)
        file_path = request.POST.get('file_path', None)
        text = request.POST.get('input_text', None)
        customer = Customer.objects.get(pk=request.user.customer.id)

        print(text)
        # データベース用のFormオブジェクトを順に作成する
        form_obj = Form(customer=customer, title=title, tag=Tag.objects.get(pk=tag_id), description=description,
                        address=address, image_url=file_path, text=text, fab_count=0)

        # 市町村の切り出し
        city = translate_address_to_city(address)
        form_obj.city = city
        print(city)

        # 住所から緯度経度情報を取得
        location = GetLocation(address)
        #location = Location(lat=random.randrange(100), lon=random.randrange(100))
        location.save()
        form_obj.location = location
        form_obj.save()

        contexts = {
            'spot_id': form_obj.id,
        }
        return render(request, "map/form_end.html", contexts)
    else:
        raise Http404


# スポットの詳細ページを表示する関数
@login_required
def show_form_detail(request, id):
    # idでスポットを検索する(Formテーブルから)
    spot = Form.objects.get(id=id)
    # contextsに検索により手に入れたスポットを組み込む({'spot': spot})
    contexts = {
        "spot": spot}
    # htmlの表示(コメントアウトを外せばOK)
    return render(request, 'map/spot_detail.html', contexts)


# route.htmlを表示する関数
@login_required
def show_route(request):
    # 全てのスポットを取得
    spots = Form.objects.all().order_by('id') \
        .values('id', 'title', 'tag__name', 'description', 'image_url', 'fab_count', 'location__lon', 'location__lat')
    spots = list(map(none_to_str, spots))

    template_name = "map/route.html"
    tag_list = Tag.objects.all()
    contexts = {
        'tag_list': tag_list,
        'spots': spots,
    }
    return render(request, template_name, contexts)


# 以下API(非同期)処理関数
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


# タグからスポットを検索
@login_required
def search_spot(request):
    search_tag_id = request.POST.get('tag', None)
    #print(search_tag_id)
    if (search_tag_id is not None) & (search_tag_id != "-1"):
        try:
            tag = get_object_or_404(Tag, pk=search_tag_id)
            spots = Form.objects.filter(tag=tag)
        except Http404:
            return JsonResponse({"status": "NG", "error": "スポットが見つかりません!"})
    else:
        spots = Form.objects.all()

    # 位置情報を取得(できない場合は、あらかじめ登録したものを利用) -> {"lat": , "lng": }
    try:
        dep = [gmaps.geolocate()['location']]
    except Exception:
        customer = request.user.customer
        dep = [{"lat": customer.location.lat, "lng": customer.location.lon}]
    moving = request.POST.get('moving', None)
    print(moving)
    # スポットの距離制限
    spots = GetDistances(dep=dep, spots=spots, moving=moving)
    print(spots)
    if not spots:
        return JsonResponse({"status": "NG", "error": "スポットが見つかりません!"})
    # ランダムに1件取り出す
    spot = spots[random.randrange(len(spots))]

    return JsonResponse({"status": "OK", "spot": spot})


# 以下機能関数
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


# 今日の日付をtimezoneを考慮して返す
def get_today_aware_obj() -> datetime:
    now = localtime(timezone.now())
    # nativeで比較させる
    dt_native = datetime.datetime(now.year, now.month, now.day, 0, 0, 0, 0)
    dt_aware = make_aware(dt_native)
    return dt_aware


# Noneを空文字に変換
def none_to_str(dict_obj: dict) -> dict:
    for key, value in dict_obj.items():
        if value is None:
            dict_obj[key] = ''
    return dict_obj


# 住所から市町村を抜き出し
def translate_address_to_city(address: str):
    if not address.startswith('愛知県'):
        address = '愛知県' + address

    for target in ['市', '町', '村']:
        number = address.find(target)
        if number:
            match_obj = re.match('愛知県(.+)', address[:number + 1])
            if match_obj:
                match_obj = match_obj.group(1)
                return match_obj
    return None


# 住所から緯度経度情報に変換する関数
def GetLocation(address: str) -> Location:
    # map APIで住所問い合わせ
    result = gmaps.geocode(address)
    result_location = result[0]['geometry']['location']
    print(result_location)
    location = Location(lat=result_location['lat'], lon=result_location['lng'])
    return location


# 現在地からの距離を出す関数
def GetDistances(dep, spots, moving) -> dict:
    # map用の高速化関数
    def form_to_root(x):
        location = [{'lat': x['location__lat'], 'lng': x['location__lon']}]
        x['distance'] = gmaps.distance_matrix(dep, location)['rows'][0]['elements'][0]['distance']['value']
        return x

    dest = spots.select_related('location').values('id', 'tag__id', 'title', 'location__lat', 'location__lon')
    #print(dest)
    routes = list(map(form_to_root, dest))
    if moving == "自転車":
        routes = [route for route in routes if route['distance'] < 7000]
    elif moving == "車":
        routes = [route for route in routes if route['distance'] < 15000]
    return routes


