# Pythonのベースイメージを指定
FROM python:3.9-slim

RUN mkdir /output
RUN mkdir /app
RUN mkdir /app/dl_dir

# 作業ディレクトリを設定
WORKDIR /app

# Gitをインストール
RUN apt-get update && \
    apt-get install -y git wget libgl1-mesa-glx libglib2.0-0 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY ./app/* /app/

# リポジトリをクローン
ARG PIPELINE_DL_DEF

RUN wget "${PIPELINE_DL_DEF}" -O pipeline_download.json

RUN pip install --no-cache-dir -r dl_requirements.txt
RUN python pipeline_manager.py pipeline_download.json

RUN ls -la /app/dl_dir

WORKDIR /app/dl_dir

# 必要なPythonパッケージをインストール
RUN pip install --no-cache-dir -r requirements.txt

# pipelineを実行
RUN python pipeline_framework.py

# コンテナ実行時に結果を取得する
CMD cp -r /app/dl_dir /output
