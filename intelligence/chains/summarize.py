"""Meeting summarization chain."""
from langchain_core.prompts import ChatPromptTemplate
from intelligence.schemas import MeetingSummary


SUMMARY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a meeting analyst. Analyze the transcript and return a JSON object with exactly these fields:
- "title": short meeting title (string)
- "summary": 2-3 sentence summary (string)
- "key_points": list of main discussion points (array of strings)
- "participants": list of speaker names mentioned (array of strings)
- "duration_minutes": estimated duration in minutes or null

Return only valid JSON, no extra text."""),
    ("user", "Transcript:\n\n{transcript}")
])


async def summarize_meeting(llm, transcript: str) -> MeetingSummary:
    chain = SUMMARY_PROMPT | llm.with_structured_output(MeetingSummary)
    return await chain.ainvoke({"transcript": transcript})
