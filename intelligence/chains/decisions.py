"""Decision extraction chain."""
from langchain_core.prompts import ChatPromptTemplate
from typing import List
from pydantic import BaseModel
from intelligence.schemas import Decision


class DecisionList(BaseModel):
    items: List[Decision]


DECISIONS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a meeting analyst. Extract decisions made in the transcript.

Return a JSON object with field "items" containing an array. Each item has:
- "decision": what was decided (string, required)
- "rationale": why this decision was made (string, required)
- "participants": list of people involved (array of strings)
- "timestamp": null

If no decisions were made, return {{"items": []}}.
Return only valid JSON, no extra text."""),
    ("user", "Transcript:\n\n{transcript}")
])


async def extract_decisions(llm, transcript: str) -> List[Decision]:
    chain = DECISIONS_PROMPT | llm.with_structured_output(DecisionList)
    result = await chain.ainvoke({"transcript": transcript})
    return result.items
