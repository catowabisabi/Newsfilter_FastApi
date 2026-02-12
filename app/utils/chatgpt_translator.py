"""
ChatGPT翻譯器 - 使用OpenAI API進行翻譯和分析
"""

import os
import json
import re
from typing import Dict, Any, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

# 檢查是否有openai庫
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI library not installed. Translation will return original text.")


class ChatGPTTranslator:
    """使用ChatGPT進行翻譯和新聞分析"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.enabled = bool(self.api_key) and OPENAI_AVAILABLE
        
        if self.enabled:
            # OpenAI v1.0+ API客戶端
            self.client = openai.OpenAI(api_key=self.api_key)
            print("✅ ChatGPT Translator initialized (v1.0+ API)")
        else:
            self.client = None
            if not OPENAI_AVAILABLE:
                print("⚠️ ChatGPT Translator disabled: openai library not installed")
            else:
                print("⚠️ ChatGPT Translator disabled: OPENAI_API_KEY not set")
    
    def translate_to_chinese(self, text: str) -> str:
        """翻譯文字為繁體中文"""
        if not self.enabled or not text or not text.strip():
            return text
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": "你是一個專業翻譯員。請將以下英文翻譯成繁體中文。只輸出翻譯結果，不要加任何解釋。"
                    },
                    {"role": "user", "content": text}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"⚠️ Translation error: {e}")
            return text
    
    def translate_news(self, title: str, summary: str, title_cn: str = None, summary_cn: str = None) -> Tuple[str, str]:
        """翻譯新聞標題和摘要（如果已有中文翻譯則跳過）"""
        if not self.enabled:
            return title, summary
        
        # 檢查是否已有中文翻譯，如果有則跳過
        if title_cn and title_cn.strip() and title_cn != title:
            print(f"✅ Skip translation - title_cn already exists")
            existing_title_cn = title_cn
        else:
            existing_title_cn = None
            
        if summary_cn and summary_cn.strip() and summary_cn != summary:
            print(f"✅ Skip translation - summary_cn already exists")
            existing_summary_cn = summary_cn
        else:
            existing_summary_cn = None
            
        # 如果兩個都已存在，直接返回
        if existing_title_cn and existing_summary_cn:
            return existing_title_cn, existing_summary_cn
        
        try:
            # 只翻譯需要的部分
            if existing_title_cn:
                # 只翻譯摘要
                content = f"摘要: {summary}"
                system_prompt = """你是一個專業金融新聞翻譯員。請將以下英文摘要翻譯成繁體中文。
請以JSON格式輸出：{"summary_cn": "翻譯後摘要"}
只輸出JSON，不要其他內容。"""
                expected_key = "summary_cn"
                fallback = (existing_title_cn, summary)
            elif existing_summary_cn:
                # 只翻譯標題
                content = f"標題: {title}"
                system_prompt = """你是一個專業金融新聞翻譯員。請將以下英文標題翻譯成繁體中文。
請以JSON格式輸出：{"title_cn": "翻譯後標題"}
只輸出JSON，不要其他內容。"""
                expected_key = "title_cn"
                fallback = (title, existing_summary_cn)
            else:
                # 兩個都翻譯
                content = f"標題: {title}\n\n摘要: {summary}"
                system_prompt = """你是一個專業金融新聞翻譯員。請將以下英文新聞翻譯成繁體中文。
請以JSON格式輸出：{"title_cn": "翻譯後標題", "summary_cn": "翻譯後摘要"}
只輸出JSON，不要其他內容。"""
                expected_key = None
                fallback = (title, summary)
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                max_tokens=1500,
                temperature=0.3
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # 嘗試解析JSON
            try:
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    
                    if expected_key == "title_cn":
                        return result.get("title_cn", title), existing_summary_cn
                    elif expected_key == "summary_cn":
                        return existing_title_cn, result.get("summary_cn", summary)
                    else:
                        return result.get("title_cn", title), result.get("summary_cn", summary)
            except json.JSONDecodeError:
                pass
            
            return fallback
            
        except Exception as e:
            print(f"⚠️ News translation error: {e}")
            return title, summary
    
    def analyze_news(self, title: str, content: str) -> Dict[str, Any]:
        """使用ChatGPT分析新聞並返回評分和關鍵字"""
        if not self.enabled:
            return {"score": 0, "keywords": [], "sentiment": 0, "summary_cn": ""}
        
        try:
            system_msg = """你是一個金融分析終端，只能以JSON格式回應。
根據以下關鍵字和權重系統分析新聞並提供評分：

關鍵字權重：
- 高權重 (4分): Endpoints, Designation, Breakthrough, Pivotal, Revolutionary
- 中高權重 (3分): Phase III, Positive, Top-Line, Significant, Agreement, Partnership, Cancer, Approval Process
- 中權重 (2分): Phase II, FDA, Approval, Acquisition, Expansion, Contract, Innovation, Clinical Trial
- 低權重 (1分): Phase I, Grants, Investors, Merger, Preliminary, Development

輸出格式：
{
  "keywords": ["keyword1", "keyword2"],
  "score": 數字,
  "sentiment": -10.0到10.0之間的情緒分數,
  "summary_cn": "繁體中文摘要（一小段文字）"
}"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": f"標題: {title}\n內容: {content}"}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # 解析JSON
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    "score": result.get("score", 0),
                    "keywords": result.get("keywords", []),
                    "sentiment": result.get("sentiment", 0),
                    "summary_cn": result.get("summary_cn", "")
                }
            
            return {"score": 0, "keywords": [], "sentiment": 0, "summary_cn": ""}
            
        except Exception as e:
            print(f"⚠️ News analysis error: {e}")
            return {"score": 0, "keywords": [], "sentiment": 0, "summary_cn": ""}
