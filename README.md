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

