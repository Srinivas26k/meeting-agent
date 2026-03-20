"""Decision extraction chain."""
from langchain_core.prompts import ChatPromptTemplate
from typing import List
from intelligence.schemas import Decision


DECISIONS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert at identifying key decisions made during meetings.

Extract all significant decisions from the transcript. For each decision:
- What was decided
- The rationale or reasoning behind it
- Who was involved in making the decision
- When in the meeting it occurred (if timestamps available)

Focus on concrete decisions, not just discussion points. A decision is a commitment to a specific course of action or resolution of an issue."""),
    ("user", "Meeting transcript:\n\n{transcript}")
])


def create_decisions_chain(llm):
    """Create the decisions extraction chain."""
    chain = DECISIONS_PROMPT | llm.with_structured_output(List[Decision])
    return chain


async def extract_decisions(llm, transcript: str) -> List[Decision]:
    """Extract decisions from transcript."""
    chain = create_decisions_chain(llm)
    result = await chain.ainvoke({"transcript": transcript})
    return result
