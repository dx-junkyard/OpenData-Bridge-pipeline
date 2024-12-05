# 荒尾市のデータ

## 1. 行政サービスのカタログを作成
### 1-1. ダウンロード定義の指定
```
export PIPELINE_DL_DEF="https://raw.githubusercontent.com/dx-junkyard/OpenData-Bridge-pipeline/main/LocalGovData/432041_city_arao/ServiceCatalogCreator/pipeline_download.json"
```

### 1-2. 概要解析LLMの実行形式の指定
#### アプリ版のOllamaを使用（※　基本はこちらを選択：[ここ](https://ollama.com/)から入手し、インストール）
```
export TARGET_IMAGE="001_BasicImage"
```
#### dockerコンテナのOllamaを使用（※ MacやGPU性能が低い場合は非推奨：アプリのOllamaの60倍近く時間がかかります）
```
export TARGET_IMAGE="002_LocalLLMImage"
```

### 1-3. 環境構築
```
curl -o ${TARGET_IMAGE}.tgz  https://raw.githubusercontent.com/dx-junkyard/OpenData-Bridge-pipeline/main/Docker/${TARGET_IMAGE}.tgz && tar xvzf ${TARGET_IMAGE}.tgz && cd ${TARGET_IMAGE} && docker compose build && docker compose up
```
アプリのollamaを使う場合は必要に応じてollamaにモデルを追加
```
ollama pull schroneko/llama-3.1-swallow-8b-instruct-v0.1:latest
ollama pull lucas2024/llama-3-elyza-jp-8b:q5_k_m
```

### 1-4. pipelineの実行
- 各ステップの実行on/off
  - 各ステップを実行するためには./pipeline/pipeline.yaml のskip_flg : no に変更、実行しないステップはyesを指定
  - 慣れないうちは１ステップだけ実行し、成功したら次の１ステップを実行していくことを推奨
- pipelineの修正
  - データ整形のためのコードと設定ファイル一式は./pipeline以下にあるため、必要に応じて編集
- 以下のコマンドでdockerコンテナを起動し、pipelineを実行
```
docker compose up
```

## 2. パイプライン設定仕様

`pipeline/pipeline.yaml`ファイルは、データ処理パイプラインのステップを設定するために使用されます。以下は、`pipeline.yaml`ファイルで使用される構造とパラメータの仕様です。

### 構造

パイプライン設定は、パイプラインの一部として実行される特定のタスクを定義するステップのリストで構成されます。ステップは、ファイルに定義されている順序で実行されます。

```yaml
steps:
  - name: <ステップ名>
    type: <ステップタイプ>
    <パラメータ1>: <値>
    <パラメータ2>: <値>
    ...
```

### パラメータ

以下の表は、`pipeline/pipeline.yaml`で使用できる各パラメータの説明です。

| パラメータ           | 説明                                                                                        | 対応type  |
|-------------------|-------------------------------------------------------------------------------------------|:----:|
| `name`            | ステップの名前。識別およびログ記録の目的で使用されます。（任意の文字列）                          | (All)  |
| `type`            | ステップのタイプで、Python実装内の特定のクラスに対応します。[ここで定義されているタイプのみ使用可](https://github.com/dx-junkyard/OpenData-Bridge-pipeline/blob/main/app/pipeline/pipeline_framework.py#L16-L24)             | -  |
| `start_url`       | Webスクレイピングステップの開始URL。                                                       | web_scraper_step |
| `user_agent`      | Webスクレイピングリクエストに使用するUser Agent文字列。                                      | web_scraper_step |
| `output_dir`      | ステップからの出力ファイルを保存するディレクトリ。                                            | (All) |
| `progress_file`   | 中断の場合に再開可能にするため、ステップの進行状況を追跡するJSONファイル。                               | web_scraper_step, service_catalog_creator_step |
| `save_every`      | 進行状況を保存する頻度（処理されたアイテムの数）を示します。                                      | web_scraper_step |
| `skip_flg`        | ステップをスキップするかどうかを示すフラグ。`yes`に設定するとステップがスキップされます。              | (All) |
| `input_json_path` | 入力データが必要なステップの入力JSONファイルのパス。                                         | (All) |
| `output_json_path`| ステップ結果を保存する出力JSONファイルのパス。                                               | (All) |


#### パラメータ設定での注意点

- `skip_flg`パラメータにより、ステップの条件付き実行が可能となり、テストや条件付きワークフローに便利です。
- パラメータ`start_url`、`user_agent`、`output_dir`、`progress_file`、`save_every`、`input_json_path`、`output_json_path`、および`n_clusters`は、実行されるステップのタイプに特有のものであり、すべてのステップに適用されるわけではありません。
- この仕様書でカバーされていないパラメータや振る舞いについては、別途文書化されているか、パイプライン開発者に確認する必要があります。



### 注意点
- 上記の手順どおり実行市た場合、指定サイト内のファイル収集が完了するまで止まりません。Macであれば control + c 等で適当なところで中断させてください。
- 処理結果は100ダウンロード単位でprogress.jsonに途中経過が記録され、"docker compose up"で中断したところから再開します。
- ある程度ファイルが溜まった段階で、[./pipeline/pipeline.yamlのskip_flg](https://github.com/dx-junkyard/OpenData-Bridge-pipeline/blob/ura/LocalGovData/432041_city_arao/ServiceCatalogCreator/pipeline/pipeline.yaml#L9)の値をyesもしくは項目削除することで、スクレイピングをスキップし、ダウンロード済のファイルをもとにカタログ作成に移行することができます。

