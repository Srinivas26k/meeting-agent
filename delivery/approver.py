"""Human-in-the-loop approval logic."""
from typing import Optional
from intelligence.schemas import MeetingIntelligence
import json


class Approver:
    """Handle approval workflow for meeting intelligence."""
    
    @staticmethod
    def needs_approval(intelligence: MeetingIntelligence) -> bool:
        """
        Determine if intelligence needs human approval.
        
        Currently always returns True for safety.
        Could be enhanced with confidence scoring.
        """
        return True
    
    @staticmethod
    def format_for_review(intelligence: MeetingIntelligence) -> dict:
        """
        Format intelligence data for review UI.
        
        Returns:
            Dictionary suitable for JSON serialization
        """
        return {
            'summary': {
                'title': intelligence.summary.title,
                'summary': intelligence.summary.summary,
                'key_points': intelligence.summary.key_points,
                'participants': intelligence.summary.participants,
                'duration_minutes': intelligence.summary.duration_minutes
            },
            'action_items': [
                {
                    'task': item.task,
                    'owner': item.owner,
                    'deadline': item.deadline,
                    'priority': item.priority,
                    'context': item.context
                }
                for item in intelligence.action_items
            ],
            'decisions': [
                {
                    'decision': dec.decision,
                    'rationale': dec.rationale,
                    'participants': dec.participants,
                    'timestamp': dec.timestamp
                }
                for dec in intelligence.decisions
            ],
            'transcript': intelligence.transcript[:1000] + "..." if len(intelligence.transcript) > 1000 else intelligence.transcript
        }
    
    @staticmethod
    def apply_edits(
        intelligence: MeetingIntelligence,
        edits: dict
    ) -> MeetingIntelligence:
        """
        Apply human edits to intelligence data.
        
        Args:
            intelligence: Original intelligence
            edits: Dictionary of edits from approval UI
            
        Returns:
            Updated intelligence
        """
        # This would apply edits from the approval UI
        # For now, just return the original
        # In a full implementation, this would merge the edits
        return intelligence
