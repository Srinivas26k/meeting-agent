"""Action item extraction chain."""
from langchain_core.prompts import ChatPromptTemplate
from typing import List
from pydantic import BaseModel
from intelligence.schemas import ActionItem


class ActionItemList(BaseModel):
    items: List[ActionItem]


ACTION_ITEMS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert at extracting action items from meeting transcripts.

Identify all tasks, commitments, and follow-ups mentioned in the meeting. For each action item, extract:
- The specific task to be done
- Who is responsible (if mentioned)
- Any deadline mentioned
- Priority level (low/medium/high based on urgency and importance)
- Context explaining why this action item exists

Be thorough but only include genuine action items, not general discussion points.
If there are no action items, return an empty list."""),
    ("user", "Meeting transcript:\n\n{transcript}")
])


def create_action_items_chain(llm):
    return ACTION_ITEMS_PROMPT | llm.with_structured_output(ActionItemList)


async def extract_action_items(llm, transcript: str) -> List[ActionItem]:
    chain = create_action_items_chain(llm)
    result = await chain.ainvoke({"transcript": transcript})
    return result.items
