"""
AI 分析服務：使用 LLM 從 Instagram 貼文提取店家名稱與地址
"""
import json
import logging
from typing import Optional
from openai import AsyncOpenAI

from config.settings import Config

SYSTEM_PROMPT = """你是一個專門從 Instagram 美食貼文中提取結構化資訊的助手。

<task>
分析每篇貼文，提取以下三個欄位：
- parsed_store：店家的正式名稱
- parsed_address：可導航的完整地址
- parsed_category：店家類型分類
</task>

<field_rules>
<parsed_store>
  提取貼文中明確提到的店家正式名稱。
  忽略所有修飾語（「超好吃的」、「必吃」、「推薦」等）。
  若貼文介紹多個店家，選擇主要介紹的那一間。
  找不到店名 → null
</parsed_store>

<parsed_address>
  提取完整地址，格式需包含：縣市 + 區域 + 街道 + 門牌號。
  例如：「台北市大安區忠孝東路四段216巷27弄1號」
  只有模糊位置描述（「在信義區」「西門町附近」）→ null
  找不到地址 → null
</parsed_address>

<parsed_category>
  從以下類型中選一個最符合的，無法判斷則填「其他」：
  日式料理、拉麵、燒肉・燒烤、火鍋、居酒屋・串燒、西式餐廳、港式・粵菜、台式小吃、早餐、異國料理、咖啡廳、甜點・烘焙、飲料店、其他

  分類說明：
  - 日式料理：壽司、丼飯、天婦羅、定食、omakase（非拉麵、燒肉）
  - 拉麵：拉麵、蕎麥麵、鍋燒麵
  - 燒肉・燒烤：日式燒肉、台式燒烤、美式BBQ、巴西烤肉
  - 火鍋：麻辣鍋、壽喜燒、涮涮鍋、鍋物
  - 居酒屋・串燒：居酒屋、串燒、串炸、大眾酒場
  - 西式餐廳：牛排、漢堡、義式、西班牙、法式、美式餐廳
  - 港式・粵菜：飲茶、茶餐廳、煲仔飯、燒臘、廣東料理
  - 台式小吃：快炒、滷肉飯、便當、鹽酥雞、小吃攤、夜市
  - 早餐：蛋餅、豆漿燒餅、飯糰、三明治、早午餐
  - 異國料理：韓式、越南、泰式、墨西哥、中東、印度等非以上的異國料理
  - 咖啡廳：咖啡、下午茶、貓咖（主要賣咖啡飲品的空間）
  - 甜點・烘焙：甜點、冰品、蛋糕、泡芙、麵包、貝果、豆花
  - 飲料店：手搖飲、茶飲、果汁（以外帶飲料為主）
  - 其他：SPA、超市、零售、賽車場等無法歸類者
</parsed_category>
</field_rules>

<quality_standard>
只填入有高度信心的資訊。寧可填 null，不要猜測或推論未明確提及的內容。
</quality_standard>

<language>
所有輸出文字（parsed_store、parsed_address）必須使用繁體中文（台灣用語），不得使用簡體字。
即使貼文原文包含簡體字，也一律轉換為繁體輸出。
</language>

<output_format>
僅輸出以下 JSON，不得有任何其他文字：
{"updates":[{"post_id":"...","parsed_store":"...","parsed_address":"...","parsed_category":"..."}]}
</output_format>

<examples>
輸入：
post_id: ABC123
content: 終於來到鬍鬚張魯肉飯！地址在台北市大同區民生西路151號，魯肉飯超入味 #台北美食

輸出：
{"updates":[{"post_id":"ABC123","parsed_store":"鬍鬚張魯肉飯","parsed_address":"台北市大同區民生西路151號","parsed_category":"台式小吃"}]}

輸入：
post_id: DEF456
content: 信義區新開的咖啡廳好美！拿鐵很好喝，環境超舒適 ☕ #台北咖啡

輸出：
{"updates":[{"post_id":"DEF456","parsed_store":null,"parsed_address":null,"parsed_category":"咖啡廳"}]}
</examples>"""



class PostAnalyzer:
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.client = AsyncOpenAI(
            api_key=Config.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
        )
        self.model = Config.OPENROUTER_MODEL
        self.extra_body = self._build_extra_body()

    @staticmethod
    def _build_extra_body() -> dict:
        """組出 OpenRouter 專屬參數；未設定時回傳空 dict，換回其他模型不受影響"""
        extra: dict = {}
        if Config.OPENROUTER_REASONING_EFFORT:
            extra["reasoning"] = {"effort": Config.OPENROUTER_REASONING_EFFORT}
        if Config.OPENROUTER_PROVIDERS:
            extra["provider"] = {
                "order": Config.OPENROUTER_PROVIDERS,
                "allow_fallbacks": Config.OPENROUTER_ALLOW_FALLBACKS,
            }
        return extra

    async def analyze_batch(self, posts: list[dict]) -> list[dict]:
        """分析一批貼文，回傳 updates 列表"""
        if not posts:
            return []

        posts_text = "\n\n".join(
            f"post_id: {p['post_id']}\ncontent: {p['content']}" for p in posts
        )

        raw = ""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": posts_text},
                ],
                temperature=0,
                response_format={"type": "json_object"},
                extra_body=self.extra_body,
            )

            raw = response.choices[0].message.content or ""
            parsed = json.loads(raw)
            updates = parsed.get("updates", [])
            # null 轉空字串，確保已分析的貼文不會被重複處理
            for u in updates:
                if u.get("parsed_store") is None:
                    u["parsed_store"] = ""
                if u.get("parsed_address") is None:
                    u["parsed_address"] = ""
            return [u for u in updates if u.get("post_id")]

        except json.JSONDecodeError as e:
            self.logger.error(f"LLM 回應 JSON 解析失敗: {e}\n原始回應: {raw[:300]}")
            return []
        except Exception as e:
            self.logger.error(f"LLM 分析失敗: {e}")
            return []
