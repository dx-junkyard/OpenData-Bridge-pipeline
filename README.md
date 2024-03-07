## 1. 準備
### 1-1. 動作環境
- ここでは、MacもしくはLinuxを想定しています。Windows環境の場合はディレクトリの記載方法など適宜書き換えてください。
- docker-composeが必要です。dockder desctop等をインストールしておいてください。

### 1-2. 必要なファイルの取得
```
git clone https://github.com/dx-junkyard/OpenData-Bridge-pipeline.git
```

## 2. 実行
### 以下のコマンドにより、pipeline.yamlとdownload_config.jsonの記載内容をもとに処理が実行されます
```
cd OpenData-Bridge-pipeline
docker-compose build
docker-compose up
```

## 3. 編集
データ整形のためのコードと設定ファイル一式は./pipelineの下に配置されます。必要に応じて編集し、以下のコマンドで処理を実行します。
```
docker-compose up
```

## 4. 注意事項
現在、実行できるのは射水市の人口データの整形のみです。その他は随時追加していきます。
