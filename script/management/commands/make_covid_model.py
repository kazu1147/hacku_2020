# BaseCommandを継承して作成
import configparser
import os

from django.core.management import BaseCommand
import requests
import datetime
import json
import numpy as np
import pandas as pd
from django.utils import timezone
from django.utils.timezone import localtime, make_aware

from map.models import Covid_level
import matplotlib.pyplot as plt
import re
from sklearn.ensemble import RandomForestRegressor
# ランダムサーチ
from sklearn.model_selection import RandomizedSearchCV
from sklearn.metrics import r2_score

from project.settings import BASE_DIR


class Command(BaseCommand):
    # python manage.py help count_entryで表示されるメッセージ
    help = ''
    conf = configparser.ConfigParser()
    settingsFilePath = os.path.join(BASE_DIR, "settings.ini")
    conf.read_file(open(settingsFilePath, "r"))

    # コマンドライン引数を指定します。(argparseモジュール https://docs.python.org/2.7/library/argparse.html)
    # 今回は無し
    # def add_arguments(self, parser):
    # parser.add_argument('blog_id', nargs='+', type=int)

    # コマンドが実行された際に呼ばれるメソッド
    def handle(self, *args, **options):
        print("感染者予測モデルの作成と予測を開始...")
        print("データをスクレイピング中...")
        covid_dict = self.get_covid_dict_by_scraping(url=self.conf['scraping']['url'])
        print("スクレイピング完了")
        print("データを加工中...")
        self.preprocessing_process(covid_dict=covid_dict)
        print("加工完了")
        print("モデルの作成中...")
        model = self.create_model()
        print("モデルの作成完了")
        print("モデルの推論中...")
        val_pred = model.predict(self.X_valid)
        y_pred = model.predict(self.test)
        print(y_pred)
        print("結果をdbに格納中...")
        self.put_predict_data(y_pred)
        print("結果の格納完了")
        print("モデルの推論完了")
        print("全て完了")

    # スクレイピング結果を収集する
    @staticmethod
    def get_covid_dict_by_scraping(url: str) -> dict:
        req = requests.get(url, timeout=15)
        covid_dict = json.loads(req.text)
        return covid_dict["patients"]["data"]

    # 感染者予測のための前処理を行う
    def preprocessing_process(self, covid_dict: dict):
        df = pd.DataFrame(covid_dict)
        df.drop(["No", "接触状況", "w", "short_date", "発表日", "年代・性別", "国籍", "備考"], axis=1, inplace=True)
        # 愛知県の市町村以外は削除
        df_aichi = pd.read_csv("aichi.csv", encoding="s-jis")
        true_areas = df_aichi["area"].values
        for check_area in df["住居地"].values:
            if check_area not in true_areas:
                df = df[df["住居地"] != check_area]
        city_area_map_df = pd.read_csv("city_area_map.csv", encoding="s-jis", engine="python")
        df.rename(columns={"住居地": "city"}, inplace=True)
        df = pd.merge(df, city_area_map_df, how="left")
        df.drop("city", axis=1, inplace=True)
        df.sort_values(by=['area_number', 'date'], inplace=True)
        df['infection_num'] = 1
        df['infection_num'] = df.groupby(['area_number', 'date'])['infection_num'].transform('sum')
        df = df[~df.duplicated()]
        df["date"] = pd.to_datetime(df["date"])
        # 最も古い日から新しい日のエリアごと日にちごとのdfを作成する
        date_min = df["date"].min()
        date_max = df["date"].max() + datetime.timedelta(days=1)
        df_fill_date = pd.DataFrame()

        for i in range(1, 14):
            df_buff = pd.DataFrame({'area_number': i},
                                   index=pd.date_range(date_min, date_max, freq='D'))
            df_fill_date = pd.concat([df_fill_date, df_buff])
        df_fill_date.reset_index(inplace=True)
        df_fill_date.rename(columns={"index": "date"}, inplace=True)
        df_target = pd.merge(df_fill_date, df, on=["area_number", "date"], how="left")
        df_target.fillna(0, inplace=True)
        for i in [1, 2, 3, 4, 7, 14]:
            # 単純shift
            df_target[f"infection_num_prev_{i}"] = \
                df_target.groupby("area_number")["infection_num"] \
                    .transform(lambda x: x.shift(i))

            # 単純移動平均
            if i != 1:
                df_target[f"infection_num_rolling_mean_1_{i}"] = \
                    df_target.groupby("area_number")["infection_num"] \
                        .transform(lambda x: x.shift(1).rolling(i).mean())

            # 単純移動標準偏差
            if i != 1:
                df_target[f"infection_num_rolling_std_1_{i}"] = \
                    df_target.groupby("area_number")["infection_num"] \
                        .transform(lambda x: x.shift(1).rolling(i).std())

        df_target.dropna(inplace=True)

        # 曜日の考慮
        attrs = [
            "month",
            "week",
            "day",
            "dayofweek",
        ]

        for attr in attrs:
            dtype = np.int16 if attr == "year" else np.int8
            df_target[attr] = getattr(df_target["date"].dt, attr).astype(dtype)

        df_target["is_weekend"] = df_target["dayofweek"].isin([5, 6]).astype(np.int8)

        date_max_minus = date_max + datetime.timedelta(days=-1)
        valid = df_target.loc[df_target["date"] == date_max_minus, :]
        train = df_target.loc[(df_target["date"] != date_max) & \
                              (df_target["date"] != date_max_minus), :]
        test = df_target.loc[df_target["date"] == date_max, :]

        use_features = df_target.columns.drop(["date", "infection_num"])
        #print(train)

        self.X_train = train[use_features]
        self.y_train = train["infection_num"]
        self.X_valid = valid[use_features]
        self.val_answear = valid["infection_num"]
        self.test = test[use_features]

    # 感染者予測のモデルを作成する
    def create_model(self):
        rfr = RandomForestRegressor(random_state=32)
        rfr.fit(self.X_train, self.y_train)
        return rfr

    # 結果をdbに格納する
    def put_predict_data(self, y_pred: list):
        covid_obj = Covid_level()
        keys = [obj.name for obj in Covid_level._meta.get_fields()]
        # 時間(何月何日何時の定期実行かを把握->awareで！)
        today = localtime(timezone.now())
        values = [today]
        for val in y_pred:
            if val > 10:
                level = 5
            elif val > 5:
                level = 4
            elif val > 1:
                level = 3
            elif val > 0.3:
                level = 2
            else:
                level = 1
            values.append(level)
        for field, value in zip(keys, values):
            setattr(covid_obj, field, value)
        covid_obj.save()



