## 1. 動作環境
- ここでは、MacもしくはLinuxを想定しています。Windows環境の場合はディレクトリの記載方法など適宜書き換えてください。
- docker-composeが必要です。dockder desctop等をインストールしておいてください。


## 2. 実行内容の指定
### 2-1. 射水市の人口データ整形処理
```
export PIPELINE_DL_DEF="https://raw.githubusercontent.com/dx-junkyard/OpenData-Library/main/LocalGovData/162116_city_imizu/PopulationData/pipeline_download.json"
```

## 3. 必要なファイルの取得&初回実行
```
git clone https://github.com/dx-junkyard/OpenData-Bridge-pipeline.git && cd OpenData-Bridge-pipeline && docker-compose build && docker-compose up
```

## 4. 結果確認
pipeline, input_dir, output_dirの３つのディレクトリが追加されます。
- pipeline : OpenDataProcCodeLab から取得したソースコードと処理定義が配置されます
- input_dir : 入力フィアルがここに配置されます（射水市の人口データ処理の場合は射水市のサイトからダウンロードした人口データに関するPDFが配置されます）
- output_dir : 処理結果がここに配置されます（射水市の人口データ処理の場合は、処理結果のcsvがここに配置されます）

## 5. 試行錯誤
### 5-1. 処理の変更
データ整形のためのコードと設定ファイル一式は./pipelineの下に配置されます。必要に応じて編集してください
### 5-2. 再実行
以下のコマンドでコンテナを起動し、処理を再度実行します。
```
docker-compose up
```
### 5-3. Dockerイメージの作り直しが必要な場合
以下を実行してください
```
sh reset.sh
```


