1th env
====

### hacku_2020 環境構築
(1) anacondaダウンロード  

(2) hacku_2020の環境を作成  
->python==3.7.0で指定する

(3) anaconda promptを開く

(4) 以下で必要なライブラリをインストール  
-pip install -r requirements.txt  
-conda install -c anaconda postgresql=9.6.6  

(5)  
・C:\Users\local\anaconda3\envs\optfit\Dataのパスに対し、initdbを実行。(localは、自PCのユーザ名)  
->これにより、postgresデータベースができる。  
-pg_ctl -D "C:\Users\local\anaconda3\envs\optfit\Data" -l logfile start  
によりdbを起動。  
-psql -h localhost -p 5432 -U postgres -d postgres  
によりdbに接続。  
->初期状態ではpostgresユーザ(role)とpostgresデータベースが作成されるため、
-Uオプションと-dオプションでユーザとデータベースを設定している。  
->パスワードが求められたら、postgresを入力  
※繋がらない場合
恐らく、ユーザ名が*(自PCのユーザ名)になっているため、以下を実施  
-psql -h localhost -p 5432 -U * -d postgresによりdbに接続。  
-create role postgres with superuser login password 'postgres';  
-alter role postgres createdb;  
->これで、psql -h localhost -p 5432 -U postgres -d postgresに繋がるようになる。  
->\qでdbから抜けてpsql -h localhost -p 5432 -U postgres -d postgresでdbに接続


db準備-2(postgresqlのvelduce作成)  
※postgresデータベースにpostgresロールでアクセスしている前提  
-create database velduce;  
で、velduceデータベースを作成し、\qでdbから抜ける  

<postgres 主要コマンド>  
\q:dbのプロンプトから脱出  
\l:データベース一覧を表示()  
\du:ユーザ(role)と権限の一覧  
\n:スキーマ(後述)の一覧  
\t:テーブルの一覧  

(6)pycharm(開発に使うエディタ)をダウンロード  
https://www.jetbrains.com/pycharm/より


(7)pycharmの起動  
・VelDuceフォルダ(プロジェクト)を選択し、開く  
・「ファイル」->「設定」->「プロジェクト」->「プロジェクトインタプリタ」と辿る  
・「プロジェクトインタプリタ」として、2でanacondaから作成したhacku_2020環境を選択  
->これにより、プロジェクトとanaconda環境が紐づく(インストールしたライブラリなども利用可能になる)
  
(8)python manage.py runserverで起動  










