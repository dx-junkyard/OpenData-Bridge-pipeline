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
├── scrapy.cfg
└── src/
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

プロジェクトのルートディレクトリ (`opendata_bridge`) に移動してコマンドを実行します。

#### 江戸川区 (Edogawa)
基本的なクローリングを行います。
```bash
cd opendata_bridge
scrapy crawl edogawa -O output_edogawa.jsonl
```

#### 国分寺市 (Kokubunji)
LLMを使用してHTMLを解析するため、OpenAI互換のAPIキーが必要です。
環境変数を設定してから実行してください。

```bash
cd opendata_bridge

# 環境変数の設定 (例)
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="https://api.openai.com/v1" # 必要な場合
export LLM_MODEL="gpt-4-turbo-preview"

# スパイダーの実行
scrapy crawl kokubunji -O output_kokubunji.jsonl
```

**注意:** 国分寺市のスパイダーはLLM APIを呼び出すため、実行に時間がかかる場合があり、API利用料が発生する可能性があります。

### 設定 (Configuration)
`opendata_bridge/src/settings.py` で基本的な設定を変更できます。
- `DOWNLOAD_DELAY`: クローリングの待機時間
- `CONCURRENT_REQUESTS`: 並列リクエスト数

### 開発時の注意
- `__pycache__` などのキャッシュファイルはコミットしないでください。
- スパイダーを追加する場合は、`src/spiders/base_spider.py` の `BaseSpider` を継承することを推奨します。
