"""Intelligence pipeline orchestrator."""
import asyncio
import yaml
import os
from intelligence.schemas import MeetingIntelligence, MeetingSummary
from intelligence.chains.summarize import summarize_meeting
from intelligence.chains.action_items import extract_action_items
from intelligence.chains.decisions import extract_decisions


class IntelligencePipeline:
    """Orchestrate all intelligence extraction chains."""

    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        self.llm_config = config['llm']
        self.llm = self._create_llm()

    def _create_llm(self):
        provider = self.llm_config['provider']
        model = self.llm_config['model']
        temperature = self.llm_config.get('temperature', 0.3)

        if provider == 'ollama':
            from langchain_ollama import ChatOllama
            return ChatOllama(
                model=model,
                temperature=temperature,
                # format="json" tells Ollama to always return valid JSON
                format="json",
            )
        elif provider == 'anthropic':
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model=model,
                temperature=temperature,
                max_tokens=self.llm_config.get('max_tokens', 4000),
                api_key=os.getenv('ANTHROPIC_API_KEY')
            )
        elif provider == 'openai':
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=model,
                temperature=temperature,
                max_tokens=self.llm_config.get('max_tokens', 4000),
                api_key=os.getenv('OPENAI_API_KEY')
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    async def process(self, transcript: str) -> MeetingIntelligence:
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
        summary, action_items, decisions = await asyncio.gather(
            summarize_meeting(self.llm, transcript),
            extract_action_items(self.llm, transcript),
            extract_decisions(self.llm, transcript)
        )

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
        return asyncio.run(self.process(transcript))
