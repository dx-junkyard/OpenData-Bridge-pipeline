## 1. 動作環境
- ここでは、MacもしくはLinuxを想定しています。Windows環境の場合はディレクトリの記載方法など適宜書き換えてください。
- docker-composeが必要です。dockder desctop等をインストールしておいてください。

## 2. 必要なファイルの取得&初回実行
```
git clone https://github.com/dx-junkyard/OpenData-Bridge-pipeline.git && cd OpenData-Bridge-pipeline && docker-compose build && docker-compose up
```

## 2. 編集
データ整形のためのコードと設定ファイル一式は./pipelineの下に配置されます。必要に応じて編集し、以下のコマンドで処理を実行します。
```
docker-compose up
```

## 3. 注意事項
現在、実行できるのは射水市の人口データの整形のみです。その他は随時追加していきます。
