# Pythonのベースイメージを指定
FROM python:3.9-slim

RUN mkdir /work
RUN mkdir /app
RUN mkdir /app/pipeline
RUN mkdir /app/pipeline/lib

# 作業ディレクトリを設定
WORKDIR /app

# 必要なパッケージをインストール
RUN apt-get update && \
    apt-get install -y git wget curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


COPY ./app/* /app/


# リポジトリをクローン
ARG PIPELINE_DL_DEF

RUN wget "${PIPELINE_DL_DEF}" -O pipeline_download.json

# 必要なPythonライブラリをインストール
RUN pip install --no-cache-dir -r dl_requirements.txt

RUN python pipeline_manager.py pipeline_download.json


WORKDIR /work





