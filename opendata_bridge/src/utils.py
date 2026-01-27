import json
import logging
from typing import Optional, List, Dict, Any
from openai import OpenAI

class LLMHtmlConverter:
    """
    Utility class to convert HTML to JSON using OpenAI API.
    Adapted from original pipeline logic.
    """
    def __init__(self, llm_url: str, llm_api_key: str, llm_model: str, llm_prompt: str):
        self.llm_url = llm_url
        self.llm_api_key = llm_api_key
        self.llm_model = llm_model
        self.llm_prompt = llm_prompt

        if self.llm_api_key:
            self.client = OpenAI(
                base_url=self.llm_url,
                api_key=self.llm_api_key,
            )
        else:
            self.client = None
            logging.warning("OpenAI API Key is not provided. LLM features will be disabled.")

    def convert_html_to_json(self, html_content: str) -> Optional[List[Dict[str, Any]]]:
        """
        Sends HTML content to LLM and parses the JSON response.
        """
        if not self.client:
            logging.error("OpenAI Client is not initialized (missing API Key). Skipping LLM call.")
            return None

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
                            logging.error(f"JSON parsing failed: {e}")
                            logging.error(f"Problematic JSON string: {json_str}")
                            return None

                logging.error(f"No valid JSON array found in response: {response}")
                return None

            except Exception as e:
                logging.error(f"Failed to extract JSON: {str(e)}")
                return None

        except Exception as e:
            logging.error(f"LLM call failed: {str(e)}")
            return None
