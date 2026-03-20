"""Pydantic schemas for structured outputs."""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ActionItem(BaseModel):
    """Action item extracted from meeting."""
    task: str = Field(description="The action item task description")
    owner: Optional[str] = Field(default=None, description="Person responsible")
    deadline: Optional[str] = Field(default=None, description="Deadline if mentioned")
    priority: str = Field(default="medium", description="Priority: low, medium, high")
    context: str = Field(description="Context from the meeting")


class Decision(BaseModel):
    """Decision made during meeting."""
    decision: str = Field(description="The decision that was made")
    rationale: str = Field(description="Why this decision was made")
    participants: List[str] = Field(default_factory=list, description="Who was involved")
    timestamp: Optional[float] = Field(default=None, description="When in the meeting")


class MeetingSummary(BaseModel):
    """Overall meeting summary."""
    title: str = Field(description="Meeting title/topic")
    summary: str = Field(description="Concise meeting summary (2-3 paragraphs)")
    key_points: List[str] = Field(description="Main discussion points")
    participants: List[str] = Field(default_factory=list, description="Meeting participants")
    duration_minutes: Optional[int] = Field(default=None, description="Meeting duration")


class MeetingIntelligence(BaseModel):
    """Complete meeting intelligence output."""
    summary: MeetingSummary
    action_items: List[ActionItem]
    decisions: List[Decision]
    transcript: str = Field(description="Full transcript text")
    processed_at: datetime = Field(default_factory=datetime.now)


class TranscriptSegment(BaseModel):
    """Single transcript segment with speaker."""
    speaker: str
    start: float
    end: float
    text: str
