"""SQLite database models and operations."""
from sqlmodel import SQLModel, Field, create_engine, Session, select
from typing import Optional, List
from datetime import datetime
import json


class Meeting(SQLModel, table=True):
    """Meeting record."""
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    date: datetime = Field(default_factory=datetime.now)
    duration_minutes: Optional[int] = None
    participants: str = Field(default="[]")  # JSON array
    audio_file_path: Optional[str] = None
    transcript: Optional[str] = None
    summary: Optional[str] = None
    key_points: str = Field(default="[]")  # JSON array
    action_items: str = Field(default="[]")  # JSON array
    decisions: str = Field(default="[]")  # JSON array
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Database:
    """Database operations."""
    
    def __init__(self, db_url: str = "sqlite:///meetings.db"):
        """Initialize database connection."""
        self.engine = create_engine(db_url, echo=False)
        SQLModel.metadata.create_all(self.engine)
    
    def create_meeting(self, meeting_data: dict) -> Meeting:
        """Create a new meeting record."""
        # Convert lists to JSON strings
        if 'participants' in meeting_data and isinstance(meeting_data['participants'], list):
            meeting_data['participants'] = json.dumps(meeting_data['participants'])
        if 'key_points' in meeting_data and isinstance(meeting_data['key_points'], list):
            meeting_data['key_points'] = json.dumps(meeting_data['key_points'])
        if 'action_items' in meeting_data and isinstance(meeting_data['action_items'], list):
            meeting_data['action_items'] = json.dumps(meeting_data['action_items'])
        if 'decisions' in meeting_data and isinstance(meeting_data['decisions'], list):
            meeting_data['decisions'] = json.dumps(meeting_data['decisions'])
        
        meeting = Meeting(**meeting_data)
        
        with Session(self.engine) as session:
            session.add(meeting)
            session.commit()
            session.refresh(meeting)
        
        print(f"💾 Meeting saved to database (ID: {meeting.id})")
        return meeting
    
    def get_meeting(self, meeting_id: int) -> Optional[Meeting]:
        """Get meeting by ID."""
        with Session(self.engine) as session:
            return session.get(Meeting, meeting_id)
    
    def list_meetings(self, limit: int = 50) -> List[Meeting]:
        """List recent meetings."""
        with Session(self.engine) as session:
            statement = select(Meeting).order_by(Meeting.date.desc()).limit(limit)
            return list(session.exec(statement))
    
    def update_meeting(self, meeting_id: int, updates: dict) -> Optional[Meeting]:
        """Update meeting record."""
        with Session(self.engine) as session:
            meeting = session.get(Meeting, meeting_id)
            if not meeting:
                return None
            
            for key, value in updates.items():
                if hasattr(meeting, key):
                    # Convert lists to JSON if needed
                    if key in ['participants', 'key_points', 'action_items', 'decisions']:
                        if isinstance(value, list):
                            value = json.dumps(value)
                    setattr(meeting, key, value)
            
            meeting.updated_at = datetime.now()
            session.add(meeting)
            session.commit()
            session.refresh(meeting)
            
            return meeting
    
    def delete_meeting(self, meeting_id: int) -> bool:
        """Delete meeting record."""
        with Session(self.engine) as session:
            meeting = session.get(Meeting, meeting_id)
            if not meeting:
                return False
            
            session.delete(meeting)
            session.commit()
            return True
