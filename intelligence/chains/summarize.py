"""Meeting summarization chain."""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from intelligence.schemas import MeetingSummary


SUMMARY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert meeting analyst. Analyze the meeting transcript and provide a comprehensive summary.

Extract:
1. A clear title for the meeting based on the main topic
2. A concise 2-3 paragraph summary of what was discussed
3. Key discussion points (bullet points)
4. List of participants mentioned by name

Be factual and objective. Focus on substance over style."""),
    ("user", "Meeting transcript:\n\n{transcript}")
])


def create_summary_chain(llm):
    """Create the summarization chain."""
    parser = JsonOutputParser(pydantic_object=MeetingSummary)
    
    chain = SUMMARY_PROMPT | llm.with_structured_output(MeetingSummary)
    
    return chain


async def summarize_meeting(llm, transcript: str) -> MeetingSummary:
    """Summarize a meeting transcript."""
    chain = create_summary_chain(llm)
    result = await chain.ainvoke({"transcript": transcript})
    return result
