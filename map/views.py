from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

# Create your views here.
from map.models import Form


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

    contexts = {
        "spots": spots,
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
