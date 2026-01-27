# Opendata Bridge Pipeline

## 1. 動作環境
- ここでは、MacもしくはLinuxを想定しています。Windows環境の場合はディレクトリの記載方法など適宜書き換えてください。
- docker-composeが必要です。docker desktop等をインストールしておいてください。
- Python 3.9+ が必要です。

## 2. 旧パイプライン (Deprecated)
|Title|説明|URL|備考|
|----|----|----|----|
|射水市|射水市のデータ加工pipeline <br>(deprecated)|pipelineの使い方| deprecated(データ移行先に未対応)|
|荒尾市|荒尾市の行政サービスカタログ作成pipeline <br> |[pipelineの使い方](https://github.com/dx-junkyard/OpenData-Bridge-pipeline/tree/main/LocalGovData/432041_city_arao)|タグ解析によるHTML構造解析|
|瑞穂町|瑞穂町の行政サービスカタログ作成pipeline <br> |[pipelineの使い方](https://github.com/dx-junkyard/OpenData-Bridge-pipeline/tree/main/LocalGovData/133035_town_mizuho)|タグ解析によるHTML構造解析|
|国分寺市|国分寺市の行政サービスカタログ作成pipeline <br> |[pipelineの使い方](https://github.com/dx-junkyard/OpenData-Bridge-pipeline/tree/main/LocalGovData/13214_city_kokubunji)|LLMによるHTML構造解析|

## 3. Scrapy Project Structure (New Architecture)
The project is being migrated to a standard Scrapy architecture under `opendata_bridge/`.

```text
opendata_bridge/
├── crawls/            # Job directories for resume (auto-generated)
├── output/            # Scraped data (JSONL)
├── scrapy.cfg
└── src/
    ├── main.py            # CLI Entry point
    ├── items.py           # Output data definition (OpendataBridgeItem)
    ├── middlewares.py
    ├── pipelines.py       # Data persistence logic
    ├── settings.py        # Scrapy settings
    ├── utils.py           # Shared utilities (LLM converter etc.)
    └── spiders/
        ├── __init__.py
        ├── base_spider.py # Common logic (BaseSpider)
        ├── edogawa.py     # Edogawa City Spider (13123)
        ├── kokubunji.py   # Kokubunji City Spider (13214)
        ├── kokubunji_prompt.txt # Prompt template for Kokubunji
        └── mizuho.py      # Mizuho Town Spider (133035 - Placeholder)
```

## 4. 使い方 (Usage)

### インストール (Installation)
必要なライブラリをインストールします。
```bash
pip install scrapy openai pandas
```

### スパイダーの実行 (Running Spiders)

プロジェクトのルートディレクトリで、`src/main.py` を使用して実行します。
このスクリプトは、**中断・再開機能**と**ステップ実行制御**を提供します。

#### 基本的な実行コマンド
```bash
# プロジェクトルートに移動
# PYTHONPATHを設定してモジュールを認識させる必要があります
export PYTHONPATH=$PYTHONPATH:$(pwd)/opendata_bridge
export SCRAPY_SETTINGS_MODULE=src.settings

# 江戸川区のクローリング（中断しても再開可能）
python3 opendata_bridge/src/main.py --target edogawa --step crawl

# 国分寺市のクローリング（LLM使用）
export OPENAI_API_KEY="your-api-key"
python3 opendata_bridge/src/main.py --target kokubunji --step crawl
```

#### 引数の説明
- `--target`: 対象の自治体識別子 (例: `edogawa`, `kokubunji`)
- `--step`: 実行する工程
  - `crawl`: スクレイピングを実行します。結果は `output/{target}.jsonl` に保存されます。
  - `enrich`: データ加工のみを実行します（現在はプレースホルダー）。
  - `all` (default): クロールと加工を順次実行します。

### 中断・再開機能 (Resume Capability)
`src/main.py` 経由で実行すると、自動的に `crawls/{target}` ディレクトリにクロール状態が保存されます。
実行を `Ctrl+C` で停止しても、同じコマンドを再度実行すれば、**未取得のURLから自動的に再開**されます。

### 設定 (Configuration)
`opendata_bridge/src/settings.py` で基本的な設定を変更できます。
- `DOWNLOAD_DELAY`: クローリングの待機時間
- `CONCURRENT_REQUESTS`: 並列リクエスト数

### 開発時の注意
- `__pycache__` などのキャッシュファイルはコミットしないでください。
- スパイダーを追加する場合は、`src/spiders/base_spider.py` の `BaseSpider` を継承することを推奨します。
