"""Intelligence pipeline orchestrator."""
import asyncio
from typing import Dict, List
import yaml
import os
from intelligence.schemas import MeetingIntelligence, MeetingSummary
from intelligence.chains.summarize import summarize_meeting
from intelligence.chains.action_items import extract_action_items
from intelligence.chains.decisions import extract_decisions


class IntelligencePipeline:
    """Orchestrate all intelligence extraction chains."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize pipeline with LLM from config."""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        self.llm_config = config['llm']
        self.llm = self._create_llm()
    
    def _create_llm(self):
        """Create LLM instance based on config."""
        provider = self.llm_config['provider']
        model = self.llm_config['model']
        temperature = self.llm_config.get('temperature', 0.3)
        max_tokens = self.llm_config.get('max_tokens', 4000)
        
        if provider == 'anthropic':
            from langchain_anthropic import ChatAnthropic
            api_key = os.getenv('ANTHROPIC_API_KEY')
            return ChatAnthropic(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=api_key
            )
        elif provider == 'openai':
            from langchain_openai import ChatOpenAI
            api_key = os.getenv('OPENAI_API_KEY')
            return ChatOpenAI(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=api_key
            )
        elif provider == 'ollama':
            from langchain_community.llms import Ollama
            return Ollama(
                model=model,
                temperature=temperature
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    async def process(self, transcript: str) -> MeetingIntelligence:
        """
        Run all intelligence chains in parallel.

        Args:
            transcript: Full meeting transcript text

        Returns:
            Complete meeting intelligence
        """
        if not transcript or not transcript.strip():
            print("⚠️  Empty transcript — skipping LLM extraction")
            return MeetingIntelligence(
                summary=MeetingSummary(
                    title="Untitled Meeting",
                    summary="No speech detected in the recording.",
                    key_points=[],
                    participants=[]
                ),
                action_items=[],
                decisions=[],
                transcript=transcript
            )

        print("🧠 Running intelligence pipeline...")
        
        # Run all chains in parallel
        results = await asyncio.gather(
            summarize_meeting(self.llm, transcript),
            extract_action_items(self.llm, transcript),
            extract_decisions(self.llm, transcript)
        )
        
        summary, action_items, decisions = results
        
        print(f"✅ Intelligence extraction complete:")
        print(f"   - Summary: {len(summary.key_points)} key points")
        print(f"   - Action items: {len(action_items)}")
        print(f"   - Decisions: {len(decisions)}")
        
        return MeetingIntelligence(
            summary=summary,
            action_items=action_items,
            decisions=decisions,
            transcript=transcript
        )
    
    def process_sync(self, transcript: str) -> MeetingIntelligence:
        """Synchronous wrapper for process."""
        return asyncio.run(self.process(transcript))
