"""Decision extraction chain."""
from langchain_core.prompts import ChatPromptTemplate
from typing import List
from pydantic import BaseModel
from intelligence.schemas import Decision


class DecisionList(BaseModel):
    items: List[Decision]


DECISIONS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert at identifying key decisions made during meetings.

Extract all significant decisions from the transcript. For each decision:
- What was decided
- The rationale or reasoning behind it
- Who was involved in making the decision
- When in the meeting it occurred (if timestamps available)

Focus on concrete decisions, not just discussion points.
If there are no decisions, return an empty list."""),
    ("user", "Meeting transcript:\n\n{transcript}")
])


def create_decisions_chain(llm):
    return DECISIONS_PROMPT | llm.with_structured_output(DecisionList)


async def extract_decisions(llm, transcript: str) -> List[Decision]:
    chain = create_decisions_chain(llm)
    result = await chain.ainvoke({"transcript": transcript})
    return result.items
