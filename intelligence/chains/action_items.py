"""Action item extraction chain."""
from langchain_core.prompts import ChatPromptTemplate
from typing import List
from pydantic import BaseModel
from intelligence.schemas import ActionItem


class ActionItemList(BaseModel):
    items: List[ActionItem]


ACTION_ITEMS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a meeting analyst. Extract action items from the transcript.

Return a JSON object with field "items" containing an array. Each item has:
- "task": what needs to be done (string, required)
- "owner": person responsible or null
- "deadline": deadline mentioned or null
- "priority": "low", "medium", or "high"
- "context": brief context (string, required)

If no action items exist, return {{"items": []}}.
Return only valid JSON, no extra text."""),
    ("user", "Transcript:\n\n{transcript}")
])


async def extract_action_items(llm, transcript: str) -> List[ActionItem]:
    chain = ACTION_ITEMS_PROMPT | llm.with_structured_output(ActionItemList)
    result = await chain.ainvoke({"transcript": transcript})
    return result.items
