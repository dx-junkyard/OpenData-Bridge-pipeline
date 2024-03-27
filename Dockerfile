# Pythonのベースイメージを指定
FROM python:3.9-slim

RUN mkdir /work
RUN mkdir /app

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

WORKDIR /work

CMD if [ ! -d "/work/pipeline" ]; then cp -r /app/pipeline /work/; fi && pip install --no-cache-dir -r /work/pipeline/requirements.txt && python /work/pipeline/pipeline_framework.py /work/pipeline/pipeline.yaml

