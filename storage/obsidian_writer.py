"""Obsidian markdown writer for meeting notes."""
from pathlib import Path
from datetime import datetime
from intelligence.schemas import MeetingIntelligence


class ObsidianWriter:
    """Write meeting notes as Obsidian markdown files."""
    
    def __init__(self, vault_path: str):
        """
        Initialize Obsidian writer.
        
        Args:
            vault_path: Path to Obsidian vault
        """
        self.vault_path = Path(vault_path).expanduser()
        self.vault_path.mkdir(parents=True, exist_ok=True)
    
    def write_meeting(self, intelligence: MeetingIntelligence) -> Path:
        """
        Write meeting as markdown file.
        
        Args:
            intelligence: Meeting intelligence data
            
        Returns:
            Path to created markdown file
        """
        # Generate filename
        date_str = intelligence.processed_at.strftime("%Y-%m-%d")
        safe_title = "".join(c for c in intelligence.summary.title if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{date_str} - {safe_title}.md"
        filepath = self.vault_path / filename
        
        print(f"📝 Writing to Obsidian: {filename}")
        
        # Build markdown content
        content = f"""# {intelligence.summary.title}

**Date:** {intelligence.processed_at.strftime("%Y-%m-%d %H:%M")}
**Participants:** {', '.join(intelligence.summary.participants)}
**Duration:** {intelligence.summary.duration_minutes or 'N/A'} minutes

---

## Summary

{intelligence.summary.summary}

## Key Points

"""
        
        for point in intelligence.summary.key_points:
            content += f"- {point}\n"
        
        content += "\n## Action Items\n\n"
        
        for item in intelligence.action_items:
            owner = f" (@{item.owner})" if item.owner else ""
            deadline = f" 📅 {item.deadline}" if item.deadline else ""
            content += f"- [ ] {item.task}{owner}{deadline}\n"
            content += f"  - Priority: {item.priority}\n"
            content += f"  - Context: {item.context}\n"
        
        content += "\n## Decisions\n\n"
        
        for decision in intelligence.decisions:
            content += f"### {decision.decision}\n\n"
            content += f"**Rationale:** {decision.rationale}\n\n"
            if decision.participants:
                content += f"**Participants:** {', '.join(decision.participants)}\n\n"
        
        content += "\n## Full Transcript\n\n"
        content += f"```\n{intelligence.transcript}\n```\n"
        
        # Write file
        filepath.write_text(content, encoding='utf-8')
        
        print(f"✅ Written to Obsidian: {filepath}")
        return filepath
