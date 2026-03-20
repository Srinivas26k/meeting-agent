"""Action item extraction chain."""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from typing import List
from intelligence.schemas import ActionItem


ACTION_ITEMS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert at extracting action items from meeting transcripts.

Identify all tasks, commitments, and follow-ups mentioned in the meeting. For each action item, extract:
- The specific task to be done
- Who is responsible (if mentioned)
- Any deadline mentioned
- Priority level (low/medium/high based on urgency and importance)
- Context explaining why this action item exists

Be thorough but only include genuine action items, not general discussion points."""),
    ("user", "Meeting transcript:\n\n{transcript}")
])


def create_action_items_chain(llm):
    """Create the action items extraction chain."""
    # Return a list of ActionItem objects
    chain = ACTION_ITEMS_PROMPT | llm.with_structured_output(List[ActionItem])
    return chain


async def extract_action_items(llm, transcript: str) -> List[ActionItem]:
    """Extract action items from transcript."""
    chain = create_action_items_chain(llm)
    result = await chain.ainvoke({"transcript": transcript})
    return result
