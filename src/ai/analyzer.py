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
  餐廳、咖啡廳、小吃／夜市、早餐店、火鍋／燒烤、麵包／甜點、酒吧／居酒屋、超市／零售、飯店／住宿、其他
</parsed_category>
</field_rules>

<quality_standard>
只填入有高度信心的資訊。寧可填 null，不要猜測或推論未明確提及的內容。
</quality_standard>

<output_format>
僅輸出以下 JSON，不得有任何其他文字：
{"updates":[{"post_id":"...","parsed_store":"...","parsed_address":"...","parsed_category":"..."}]}
</output_format>

<examples>
輸入：
post_id: ABC123
content: 終於來到鬍鬚張魯肉飯！地址在台北市大同區民生西路151號，魯肉飯超入味 #台北美食

輸出：
{"updates":[{"post_id":"ABC123","parsed_store":"鬍鬚張魯肉飯","parsed_address":"台北市大同區民生西路151號","parsed_category":"小吃／夜市"}]}

輸入：
post_id: DEF456
content: 信義區新開的咖啡廳好美！拿鐵很好喝，環境超舒適 ☕ #台北咖啡

輸出：
{"updates":[{"post_id":"DEF456","parsed_store":null,"parsed_address":null,"parsed_category":"咖啡廳"}]}
</examples>"""

# prefill：強制模型從 JSON 開頭繼續，避免 markdown 包裝
ASSISTANT_PREFILL = '{"updates":['


class PostAnalyzer:
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.client = AsyncOpenAI(
            api_key=Config.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
        )
        self.model = Config.OPENROUTER_MODEL

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
                    # prefill：讓模型從這裡繼續，強制輸出合法 JSON
                    {"role": "assistant", "content": ASSISTANT_PREFILL},
                ],
                temperature=0,
            )

            # 模型只輸出 prefill 之後的部分，需要補回前綴
            raw = ASSISTANT_PREFILL + (response.choices[0].message.content or "")
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
