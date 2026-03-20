"""Notion integration for writing meeting notes."""
from notion_client import Client
from typing import Optional
import os
from intelligence.schemas import MeetingIntelligence


class NotionWriter:
    """Write meeting intelligence to Notion."""
    
    def __init__(self, token: Optional[str] = None, database_id: Optional[str] = None):
        """
        Initialize Notion client.
        
        Args:
            token: Notion integration token
            database_id: Notion database ID to write to
        """
        self.token = token or os.getenv('NOTION_TOKEN')
        self.database_id = database_id or os.getenv('NOTION_DATABASE_ID')
        
        if not self.token:
            raise ValueError("Notion token required. Set NOTION_TOKEN env var.")
        if not self.database_id:
            raise ValueError("Notion database ID required. Set NOTION_DATABASE_ID env var.")
        
        self.client = Client(auth=self.token)
    
    def write_meeting(self, intelligence: MeetingIntelligence) -> str:
        """
        Write meeting to Notion database.
        
        Args:
            intelligence: Meeting intelligence data
            
        Returns:
            URL of created Notion page
        """
        print(f"📝 Writing to Notion: {intelligence.summary.title}")
        
        # Build action items blocks
        action_items_blocks = []
        for item in intelligence.action_items:
            action_items_blocks.append({
                "object": "block",
                "type": "to_do",
                "to_do": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": f"{item.task} ({item.owner or 'Unassigned'})"}
                    }],
                    "checked": False
                }
            })
        
        # Build decisions blocks
        decisions_blocks = []
        for decision in intelligence.decisions:
            decisions_blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": f"{decision.decision} - {decision.rationale}"}
                    }]
                }
            })
        
        # Create page
        page = self.client.pages.create(
            parent={"database_id": self.database_id},
            properties={
                "Name": {"title": [{"text": {"content": intelligence.summary.title}}]},
                "Date": {"date": {"start": intelligence.processed_at.isoformat()}},
            },
            children=[
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"text": {"content": "Summary"}}]}
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"text": {"content": intelligence.summary.summary}}]}
                },
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"text": {"content": "Action Items"}}]}
                },
                *action_items_blocks,
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"text": {"content": "Decisions"}}]}
                },
                *decisions_blocks,
            ]
        )
        
        url = page['url']
        print(f"✅ Written to Notion: {url}")
        return url
