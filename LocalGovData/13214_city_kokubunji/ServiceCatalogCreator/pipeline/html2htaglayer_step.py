import os
import json
import yaml
import hashlib
import pandas as pd
from bs4 import BeautifulSoup
from openai import OpenAI
import logging



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
            
            # JSON配列を抽出
            try:
                # ```json と ``` で囲まれた部分を探す
                json_start = response.find('```json')
                if json_start != -1:
                    json_end = response.find('```', json_start + 6)
                    if json_end != -1:
                        json_str = response[json_start + 7:json_end].strip()
                        try:
                            # JSONとしてパース
                            json_data = json.loads(json_str)
                            if isinstance(json_data, list):
                                return json_data
                            else:
                                # 単一のオブジェクトの場合は配列に変換
                                return [json_data]
                        except json.JSONDecodeError as e:
                            logging.error(f"JSONのパースに失敗しました: {e}")
                            logging.error(f"問題のあるJSON文字列: {json_str}")
                            return None
                
                logging.error(f"有効なJSON配列が見つかりませんでした: {response}")
                return None
                
            except Exception as e:
                logging.error(f"JSONの抽出に失敗しました: {str(e)}")
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
        
        # 何回毎に保存するか？ 
        self.save_every = step_config.get('save_every', 10)
        
        # 対象divの設定
        self.target_div = step_config.get('target_div', 'voice')  # デフォルト値として'voice'を設定
        
        # リトライ対象のエラーファイルパス
        self.retry_error_file_path = step_config.get('retry_error_files', f'{self.output_json_dir}/error_urls.json')
        
        # LLMコンバーターの初期化
        self.llm_converter = LLMHtmlConverter(
            self.llm_url,
            self.llm_api_key,
            self.llm_model,
            self.llm_prompt_file
        )
        
        os.makedirs(self.output_json_dir, exist_ok=True)
        # エラーURLリストを初期化
        self.error_urls = []
        # スキップURLリストを初期化
        self.skipped_urls = []
        # 既存のエラーリストとスキップリストを読み込む
        self.load_error_urls()
        self.load_skipped_urls()

    def load_mapping(self):
        with open(self.progress_json_path, 'r') as file:
            data = json.load(file)
        return data.get("visited", {})

    def get_last_processed_url(self):
        """既存のJSONファイルから最後に処理されたURLを取得"""
        output_file = f'{self.output_json_dir}/service_catalog.json'
        if not os.path.exists(output_file):
            return None

        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data and isinstance(data, list) and len(data) > 0:
                    # 最後のエントリのURLを取得
                    last_entry = data[-1]
                    if 'URL' in last_entry and 'items' in last_entry['URL']:
                        return last_entry['URL']['items']
        except Exception as e:
            logging.error(f"既存のJSONファイルの読み込みに失敗しました: {e}")
        return None

    def get_start_position(self):
        """処理開始位置を取得"""
        last_url = self.get_last_processed_url()
        if last_url is None:
            return 0

        # URLマッピングのリストを取得
        url_list = list(self.url_mapping.keys())
        try:
            # 最後に処理されたURLの次の位置を探す
            last_index = url_list.index(last_url)
            return last_index + 1
        except ValueError:
            logging.warning(f"最後に処理されたURL {last_url} が見つかりませんでした。最初から処理を開始します。")
            return 0

    def generate_hash(self, details):
        if isinstance(details, pd.DataFrame):
            details_dict_list = details.to_dict(orient='records')
            details_dict_list = [{str(key): value for key, value in record.items()} for record in details_dict_list]
        else:
            details_dict_list = details

        details_str = json.dumps(details_dict_list, sort_keys=True)
        return hashlib.sha256(details_str.encode('utf-8')).hexdigest()

    def save_error_urls(self):
        """エラーURLリストをJSONファイルとして保存"""
        error_file = f'{self.output_json_dir}/error_urls.json'
        try:
            with open(error_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'error_urls': self.error_urls,
                    'error_count': len(self.error_urls),
                    'timestamp': pd.Timestamp.now().isoformat()
                }, f, ensure_ascii=False, indent=4)
            logging.info(f"エラーURLリストを保存しました。エラー数: {len(self.error_urls)}")
        except Exception as e:
            logging.error(f"エラーURLリストの保存に失敗しました: {e}")

    def load_error_urls(self):
        """既存のエラーURLリストを読み込む"""
        error_file = f'{self.output_json_dir}/error_urls.json'
        if os.path.exists(error_file):
            try:
                with open(error_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'error_urls' in data:
                        self.error_urls = data['error_urls']
                        logging.info(f"既存のエラーURLリストを読み込みました。エラー数: {len(self.error_urls)}")
            except Exception as e:
                logging.error(f"エラーURLリストの読み込みに失敗しました: {e}")

    def load_skipped_urls(self):
        """既存のスキップURLリストを読み込む"""
        skipped_file = f'{self.output_json_dir}/skipped_urls.json'
        if os.path.exists(skipped_file):
            try:
                with open(skipped_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'skipped_urls' in data:
                        self.skipped_urls = data['skipped_urls']
                        logging.info(f"既存のスキップURLリストを読み込みました。スキップ数: {len(self.skipped_urls)}")
            except Exception as e:
                logging.error(f"スキップURLリストの読み込みに失敗しました: {e}")

    def load_existing_data(self):
        """既存のJSONファイルからデータを読み込む"""
        unique_hashes = set()
        unique_services = []
        
        output_file = f'{self.output_json_dir}/service_catalog.json'
        if os.path.exists(output_file):
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    if existing_data and isinstance(existing_data, list):
                        unique_services = existing_data
                        # 既存のデータのハッシュを計算
                        for service in existing_data:
                            service_json = json.dumps(service, ensure_ascii=False, sort_keys=True)
                            unique_hashes.add(self.generate_hash(service_json))
                        logging.info(f"既存のJSONファイルを読み込みました。サービス数: {len(unique_services)}")
            except Exception as e:
                logging.error(f"既存のJSONファイルの読み込みに失敗しました: {e}")
        
        return unique_hashes, unique_services

    def save_skipped_urls(self):
        """スキップURLリストをJSONファイルとして保存"""
        skipped_file = f'{self.output_json_dir}/skipped_urls.json'
        try:
            with open(skipped_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'skipped_urls': self.skipped_urls,
                    'skipped_count': len(self.skipped_urls),
                    'timestamp': pd.Timestamp.now().isoformat()
                }, f, ensure_ascii=False, indent=4)
            logging.info(f"スキップURLリストを保存しました。スキップ数: {len(self.skipped_urls)}")
        except Exception as e:
            logging.error(f"スキップURLリストの保存に失敗しました: {e}")

    def process_single_file(self, url, filepath, unique_hashes, unique_services):
        """単一ファイルの処理を行う"""
        if filepath.endswith('.html'):
            # index.htmlと.html#を含むURLをスキップ
            if 'index.html' in url or '.html#' in url:
                logging.info(f"スキップ対象のURL: {url}")
                # スキップURLを記録
                self.skipped_urls.append({
                    'url': url,
                    'filepath': filepath,
                    'reason': 'index.html or .html# in URL',
                    'timestamp': pd.Timestamp.now().isoformat()
                })
                return unique_hashes, unique_services

            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    html_content = file.read()

                soup = BeautifulSoup(html_content, 'html.parser')
                main_div = soup.find('div', id=self.target_div)
                
                if main_div:
                    # LLMを使用してHTMLをJSONに変換
                    service_infos = self.llm_converter.convert_html_to_json(str(main_div))
                    
                    if service_infos is None:
                        # エラーURLを記録
                        self.error_urls.append({
                            'url': url,
                            'filepath': filepath,
                            'error_type': 'LLM_CONVERSION_ERROR',
                            'timestamp': pd.Timestamp.now().isoformat()
                        })
                        logging.error(f"URLの処理に失敗しました: {url}")
                        return unique_hashes, unique_services
                    
                    # 複数のサービス情報を処理
                    for service_info in service_infos:
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
            except Exception as e:
                logging.error(f"ファイル処理中にエラーが発生しました: {url}, エラー: {str(e)}")
                self.error_urls.append({
                    'url': url,
                    'filepath': filepath,
                    'error_type': 'FILE_PROCESSING_ERROR',
                    'error_message': str(e),
                    'timestamp': pd.Timestamp.now().isoformat()
                })
        
        return unique_hashes, unique_services

    def retry_error_files(self, unique_hashes, unique_services):
        """エラーファイルのリトライ処理を行う"""
        if not os.path.exists(self.retry_error_file_path):
            logging.warning(f"リトライ対象のエラーファイルが見つかりません: {self.retry_error_file_path}")
            return unique_hashes, unique_services

        try:
            with open(self.retry_error_file_path, 'r', encoding='utf-8') as f:
                error_data = json.load(f)
                if 'error_urls' not in error_data:
                    logging.error("エラーファイルの形式が不正です")
                    return unique_hashes, unique_services
                error_urls = error_data['error_urls']
        except Exception as e:
            logging.error(f"エラーファイルの読み込みに失敗しました: {e}")
            return unique_hashes, unique_services

        logging.info(f"エラーファイルのリトライ処理を開始します。対象ファイル数: {len(error_urls)}")
        
        processed_count = 0
        retry_success = []
        retry_failed = []

        for error_entry in error_urls:
            url = error_entry.get('url')
            filepath = error_entry.get('filepath')
            
            if not url or not filepath:
                logging.error(f"URLまたはファイルパスが不正です: {error_entry}")
                continue

            logging.info(f"リトライ処理を開始: {url}")
            old_hashes = set(unique_hashes)
            unique_hashes, unique_services = self.process_single_file(url, filepath, unique_hashes, unique_services)
            
            # 処理結果を記録
            if len(unique_hashes) > len(old_hashes):
                retry_success.append(error_entry)
            else:
                retry_failed.append(error_entry)
            
            processed_count += 1
            # {self.save_every}回ごとに中間状態を保存
            if processed_count % self.save_every == 0:
                logging.info(f"{processed_count}件のリトライ処理が完了しました。中間状態を保存します。")
                self.save_json(unique_services, self.output_json_dir)
                # リトライ結果をerror_urls.jsonに反映
                self.update_error_urls(retry_success, retry_failed)
                self.save_error_urls()
                self.save_skipped_urls()

        # 最終結果を保存
        self.save_json(unique_services, self.output_json_dir)
        # リトライ結果をerror_urls.jsonに反映
        self.update_error_urls(retry_success, retry_failed)
        self.save_error_urls()
        self.save_skipped_urls()

        logging.info(f"エラーファイルのリトライ処理が完了しました。成功: {len(retry_success)}件, 失敗: {len(retry_failed)}件")
        return unique_hashes, unique_services

    def update_error_urls(self, retry_success, retry_failed):
        """リトライ結果をerror_urls.jsonに反映"""
        # 成功したエントリをerror_urlsから削除
        success_urls = {entry['url'] for entry in retry_success}
        original_count = len(self.error_urls)
        self.error_urls = [entry for entry in self.error_urls if entry['url'] not in success_urls]
        removed_count = original_count - len(self.error_urls)
        logging.info(f"成功したエントリを削除しました: {removed_count}件")
        
        # 失敗したエントリを更新（タイムスタンプを更新）
        failed_urls = {entry['url'] for entry in retry_failed}
        updated_count = 0
        for entry in self.error_urls:
            if entry['url'] in failed_urls:
                entry['timestamp'] = pd.Timestamp.now().isoformat()
                entry['retry_count'] = entry.get('retry_count', 0) + 1
                updated_count += 1
        logging.info(f"失敗したエントリを更新しました: {updated_count}件")
        logging.info(f"残りのエラーエントリ数: {len(self.error_urls)}件")

    def execute(self):
        # 既存のデータを読み込む
        unique_hashes, unique_services = self.load_existing_data()
        processed_count = 0

        # エラーファイルのリトライ処理を実行
        unique_hashes, unique_services = self.retry_error_files(unique_hashes, unique_services)

        # 処理開始位置を取得
        start_position = self.get_start_position()
        url_list = list(self.url_mapping.keys())
        logging.info(f"処理対象のURL数: {len(url_list)}")
        logging.info(f"処理開始位置: {start_position}")
        
        # 開始位置から処理を実行
        for i in range(start_position, len(url_list)):
            url = url_list[i]
            filepath = self.url_mapping[url]
            
            unique_hashes, unique_services = self.process_single_file(url, filepath, unique_hashes, unique_services)
            
            processed_count += 1
            # {self.save_every}回ごとに中間状態を保存
            if processed_count % self.save_every == 0:
                logging.info(f"{processed_count}件の処理が完了しました。中間状態を保存します。")
                self.save_json(unique_services, self.output_json_dir)
                self.save_error_urls()
                self.save_skipped_urls()

        # 最終結果を保存
        self.save_json(unique_services, self.output_json_dir)
        self.save_error_urls()
        self.save_skipped_urls()

    def save_json(self, data, file_path):
        with open(f'{file_path}/service_catalog.json', "w", encoding="utf-8") as f:
            json_str = json.dumps(data, ensure_ascii=False, indent=4)
            logging.info(f"保存されたサービス数: {len(data)}")
            f.write(json_str)
