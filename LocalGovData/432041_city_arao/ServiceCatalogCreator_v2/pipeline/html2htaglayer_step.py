import os
import json
import yaml
import hashlib
import pandas as pd
from bs4 import BeautifulSoup
from lib.htag_node import  HTagNode as Node
from openai import OpenAI
import logging


class HtmlConverter:
    def __init__(self, soup, url, columns):
        self.soup = soup
        self.url = url
        self.root = Node('Root', level=0)
        self.current_node = self.root
        self.columns = columns
        self.parse_html_to_tree(self.soup.body)
        self.item_level = 6
        self.title = None
        self.sub_title = None
        self.summary = None

    def parse_html_to_tree(self, soup):
        tags = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'table', 'span', 'li'], recursive=True)
        for tag in tags:
            if tag.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                level = int(tag.name[1])  # h1 -> 1, h2 -> 2, ...
                #print(f'[node dump] {str(tag)}')
                new_node = Node(tag.get_text(strip=True), level)
                if level > self.current_node.level:
                    # 現在のノードが親ノードとして適切である場合
                    self.current_node.add_child(new_node)
                else:
                    # 新しいノードが現在のノードのレベルと同じかそれ以上の場合、適切な親を見つける
                    while self.current_node.level >= level:
                        self.current_node = self.current_node.parent
                    self.current_node.add_child(new_node)
                self.current_node = new_node  # 更新された現在のノード
            elif tag.name == 'table':
                self.current_node.add_table(tag)
            elif tag.name == 'p' or tag.name == 'span' or tag.name == 'li':
                self.current_node.add_item(tag.get_text(strip=True))

    def display_tree(self, node=None, indent=0):
        if node is None:
            node = self.root
        print(' ' * indent + repr(node))
        for child in node.children:
            self.display_tree(child, indent + 2)

    def collect_data_from_nodes(self, node=None, collected_data=None):
        if node is None:
            node = self.root
        if collected_data is None:
            collected_data = {}

        # キーワードにマッチするかどうか確認し、マッチしたらJSONデータを集める
        for key, keywords in self.columns.items():
            if node.matches_keywords(keywords):
                if node.level < self.item_level:
                    self.item_level = node.level
                collected_data[key] = {
                    'items': node.get_content()
                }
                #print(f'match collected_data={str(collected_data[key])}')

        # 子ノードも再帰的に処理
        for child in node.children:
            self.collect_data_from_nodes(child, collected_data)

        return collected_data


    def create_title(self, node=None):

        if node is None:
            node = self.root

        # 項目検出層より上
        if node.level >= self.item_level:
            return 
        elif node.level > 0 and self.title is None:
            if node.title == "":
                return
            self.title = []
            self.title.append(node.title)
            self.summary = node.get_content(th=self.item_level)

        # 子ノードも再帰的に処理
        for child in node.children:
            self.create_title(child)




class LLMHtmlConverter:
    def __init__(self, llm_url, llm_api_key, llm_model, llm_prompt_file):
        self.llm_url = llm_url
        self.llm_api_key = llm_api_key
        self.llm_model = llm_model
        self.llm_prompt = self.load_llm_prompt(llm_prompt_file)
        self.client = OpenAI(
            base_url=self.llm_url,
            api_key=self.llm_api_key,
        )
        #self.client = OpenAI()

    def load_llm_prompt(self, llm_prompt_file):
        try:
            with open(llm_prompt_file, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            logging.error(f"指定されたファイル '{llm_prompt_file}' が見つかりません。")
            return ""
        except Exception as e:
            logging.error(f"エラーが発生しました: {e}")
            return ""

    def convert_html_to_json(self, html_content):
        try:
            # HTMLの内容をLLMに送信
            prompt = f"{self.llm_prompt}\n{html_content}"
            chat_completion = self.client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {
                        'role': 'user',
                        'content': prompt,
                    }
                ]
            )
            response = chat_completion.choices[0].message.content
            
            # JSON部分のみを抽出
            try:
                # ```json と ``` で囲まれた部分を探す
                json_start = response.find('```json')
                json_end = response.find('```', json_start + 6)  # ```json の後の位置から検索
                
                if json_start != -1 and json_end != -1:
                    # JSON部分のみを抽出
                    json_str = response[json_start + 7:json_end].strip()  # ```json の後の7文字分をスキップ
                else:
                    # ```json で囲まれていない場合は、最初の { から最後の } までを探す
                    json_start = response.find('{')
                    json_end = response.rfind('}') + 1
                    if json_start != -1 and json_end != -1:
                        json_str = response[json_start:json_end]
                    else:
                        logging.error("JSON形式のデータが見つかりませんでした")
                        return None
                
                # JSONとしてパース
                json_data = json.loads(json_str)
                return json_data
                
            except json.JSONDecodeError as e:
                logging.error(f"JSONのパースに失敗しました: {e}")
                logging.error(f"抽出されたJSON文字列: {json_str}")
                return None
                
        except Exception as e:
            logging.error(f"LLMの呼び出しに失敗しました: {str(e)}")
            return None


class Html2HtagLayerStep:
    def __init__(self, step_config):
        self.progress_json_path = step_config['progress_file']
        self.output_json_dir = step_config['output_json_dir']
        self.url_mapping = self.load_mapping()
        
        # LLMの設定
        self.llm_url = step_config['llm_url']
        self.llm_api_key = step_config['llm_api_key']
        self.llm_model = step_config['llm_model']
        self.llm_prompt_file = step_config['llm_prompt_file']
        
        # LLMコンバーターの初期化
        self.llm_converter = LLMHtmlConverter(
            self.llm_url,
            self.llm_api_key,
            self.llm_model,
            self.llm_prompt_file
        )
        
        os.makedirs(self.output_json_dir, exist_ok=True)

    def load_mapping(self):
        with open(self.progress_json_path, 'r') as file:
            data = json.load(file)
        return data.get("visited", {})

    def generate_hash(self, details):
        if isinstance(details, pd.DataFrame):
            details_dict_list = details.to_dict(orient='records')
            details_dict_list = [{str(key): value for key, value in record.items()} for record in details_dict_list]
        else:
            details_dict_list = details

        details_str = json.dumps(details_dict_list, sort_keys=True)
        return hashlib.sha256(details_str.encode('utf-8')).hexdigest()

    def execute(self):
        unique_hashes = set()
        unique_services = []

        for url, filepath in self.url_mapping.items():
            if filepath.endswith('.html'):
                with open(filepath, 'r', encoding='utf-8') as file:
                    html_content = file.read()

                soup = BeautifulSoup(html_content, 'html.parser')
                main_div = soup.find('div', id='contents')
                
                if main_div:
                    # LLMを使用してHTMLをJSONに変換
                    service_info = self.llm_converter.convert_html_to_json(str(main_div))
                    
                    if service_info:
                        # URLを追加
                        service_info['URL'] = {
                            'items': url
                        }
                        
                        # 重複チェック
                        service_json = json.dumps(service_info, ensure_ascii=False, sort_keys=True)
                        service_hash = self.generate_hash(service_json)
                        
                        if service_hash not in unique_hashes:
                            unique_hashes.add(service_hash)
                            unique_services.append(service_info)

        # 結果を保存
        self.save_json(unique_services, self.output_json_dir)

    def save_json(self, data, file_path):
        with open(f'{file_path}/service_catalog.json', "w", encoding="utf-8") as f:
            json_str = json.dumps(data, ensure_ascii=False, indent=4)
            logging.info(f"保存されたサービス数: {len(data)}")
            f.write(json_str)
