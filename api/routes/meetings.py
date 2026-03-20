"""Meeting data endpoints."""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel

from storage.database import Database

router = APIRouter()
db = Database()


class MeetingResponse(BaseModel):
    """Meeting response model."""
    id: int
    title: str
    date: str
    participants: List[str]
    summary: Optional[str]


@router.get("/", response_model=List[MeetingResponse])
async def list_meetings(limit: int = 50):
    """List all meetings."""
    meetings = db.list_meetings(limit=limit)
    
    return [
        MeetingResponse(
            id=m.id,
            title=m.title,
            date=m.date.isoformat(),
            participants=eval(m.participants) if m.participants else [],
            summary=m.summary
        )
        for m in meetings
    ]


@router.get("/{meeting_id}")
async def get_meeting(meeting_id: int):
    """Get meeting details."""
    meeting = db.get_meeting(meeting_id)
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    import json
    
    return {
        "id": meeting.id,
        "title": meeting.title,
        "date": meeting.date.isoformat(),
        "duration_minutes": meeting.duration_minutes,
        "participants": json.loads(meeting.participants) if meeting.participants else [],
        "transcript": meeting.transcript,
        "summary": meeting.summary,
        "key_points": json.loads(meeting.key_points) if meeting.key_points else [],
        "action_items": json.loads(meeting.action_items) if meeting.action_items else [],
        "decisions": json.loads(meeting.decisions) if meeting.decisions else [],
        "created_at": meeting.created_at.isoformat(),
        "updated_at": meeting.updated_at.isoformat()
    }


@router.delete("/{meeting_id}")
async def delete_meeting(meeting_id: int):
    """Delete a meeting."""
    success = db.delete_meeting(meeting_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    return {"message": "Meeting deleted successfully"}
