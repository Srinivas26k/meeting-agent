"""Basic tests for Meeting Agent."""
import pytest
from pathlib import Path


def test_imports():
    """Test that all modules can be imported."""
    from capture.file_loader import FileLoader
    from processing.preprocessor import AudioPreprocessor
    from intelligence.schemas import MeetingIntelligence
    from storage.database import Database
    
    assert FileLoader is not None
    assert AudioPreprocessor is not None
    assert MeetingIntelligence is not None
    assert Database is not None


def test_file_loader_validation():
    """Test file loader validation."""
    from capture.file_loader import FileLoader
    
    # Test unsupported format
    with pytest.raises(ValueError, match="Unsupported format"):
        FileLoader.load("test.txt")
    
    # Test non-existent file
    with pytest.raises(FileNotFoundError):
        FileLoader.load("nonexistent.mp4")


def test_database_creation():
    """Test database initialization."""
    from storage.database import Database
    
    db = Database(db_url="sqlite:///:memory:")
    assert db.engine is not None
    
    # Test creating a meeting
    meeting_data = {
        'title': 'Test Meeting',
        'participants': ['Alice', 'Bob'],
        'summary': 'Test summary'
    }
    meeting = db.create_meeting(meeting_data)
    assert meeting.id is not None
    assert meeting.title == 'Test Meeting'


def test_schemas():
    """Test Pydantic schemas."""
    from intelligence.schemas import ActionItem, Decision, MeetingSummary
    
    # Test ActionItem
    item = ActionItem(
        task="Complete the report",
        owner="Alice",
        priority="high",
        context="Discussed in meeting"
    )
    assert item.task == "Complete the report"
    assert item.priority == "high"
    
    # Test Decision
    decision = Decision(
        decision="Use Python for backend",
        rationale="Team expertise",
        participants=["Alice", "Bob"]
    )
    assert decision.decision == "Use Python for backend"
    
    # Test MeetingSummary
    summary = MeetingSummary(
        title="Sprint Planning",
        summary="Discussed upcoming sprint goals",
        key_points=["Goal 1", "Goal 2"],
        participants=["Alice", "Bob"]
    )
    assert summary.title == "Sprint Planning"
    assert len(summary.key_points) == 2
