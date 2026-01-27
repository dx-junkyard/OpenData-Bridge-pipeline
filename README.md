## 1. 動作環境
- ここでは、MacもしくはLinuxを想定しています。Windows環境の場合はディレクトリの記載方法など適宜書き換えてください。
- docker-composeが必要です。dockder desctop等をインストールしておいてください。


## 2. 自治体の情報加工pipeline
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
    └── spiders/
        ├── __init__.py
        ├── base_spider.py # Common logic (BaseSpider)
        ├── edogawa.py     # Edogawa City Spider (13123)
        └── mizuho.py      # Mizuho Town Spider (133035 - Placeholder)
```

### Usage
Run spiders from the `opendata_bridge` directory:
```bash
cd opendata_bridge
scrapy crawl edogawa -O output.jsonl
```
