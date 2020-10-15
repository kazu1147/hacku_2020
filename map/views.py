from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect


# Create your views here.
from map.models import Form


@login_required
def redirect_top(request):
    return redirect('map:top')


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

    contexts = {
        "spots": spots,
    }

    return render(request, 'map/top.html', contexts)


@login_required
def show_form(request):
    return render(request, 'map/form.html')