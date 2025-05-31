import os
import json
import torch        
from transformers import BertTokenizer, BertModel 
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

import logging  # ログ出力のために追加

# ロギングの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')




class EmbeddingStep:
    def __init__(self, step_config):
        self.service_catalog_file = step_config['service_catalog_json']
        self.embeddings_file = step_config['embeddings_file']
        self.tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
        self.model = BertModel.from_pretrained('bert-base-uncased')

    # service catalog jsonの読み込み
    def load_json_data(self, file_path):
        """JSONファイルを読み込む"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    # service catalog
    def save_embeddings_to_file(self, embeddings, entries, output_file):
        """ベクトルデータをJSONファイルに保存する"""
        data = {
            'embeddings': embeddings.tolist(),
            'entries': entries
        }
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)

    # vector化した概要と対応するサービス情報をファイルに保存
    def save_embeddings_to_file(self, embeddings, entries, output_file):
        """ベクトルデータをJSONファイルに保存する"""
        data = {
            'embeddings': embeddings.tolist(),
            'entries': entries
        }
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)


    # 渡されたtextをベクトル化
    def get_embedding(self, text):
        """テキストをベクトル化する"""
        inputs = self.tokenizer(text, return_tensors='pt', max_length=512, truncation=True)
        outputs = self.model(**inputs)
        embedding = outputs.last_hidden_state.mean(dim=1)
        return embedding.detach().numpy()

    # service catalog中の全概要をvector化
    def get_overview_embeddings(self, service_catalog):
        """全ての概要をベクトル化する"""
        overview_embeddings = []
        entries = []
        total_entries = len(service_catalog)
        processed_entries = 0

        for service in service_catalog:
            # サービス内容の取得
            overview = service.get("サービス内容")
            if overview is None or overview == "なし":
                continue

            # 文字列型に変換してからembeddingを取得
            overview = str(overview)
            embedding = self.get_embedding(overview)
            overview_embeddings.append(embedding)

            # タイトルの取得
            formal_name = str(service.get("タイトル", "N/A"))

            entry = {
                'overview': overview,
                'formal_name': formal_name,
                'url': service.get("URL", {}).get("items", "N/A"),
                'target_labels': service.get("対象者ラベル", []),
                'service_labels': service.get("サービスラベル", [])
            }
            entries.append(entry)
            processed_entries += 1

        logging.info(f"処理完了: 全{total_entries}件中{processed_entries}件を処理しました。")
        return np.vstack(overview_embeddings), entries

    def execute(self):
        self.service_catalog = self.load_json_data(self.service_catalog_file)
        self.overview_embeddings, self.entries = self.get_overview_embeddings(self.service_catalog)
        if self.embeddings_file:
            self.save_embeddings_to_file(self.overview_embeddings, self.entries, self.embeddings_file)


