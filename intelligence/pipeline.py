"""
Intelligence pipeline — orchestrates all LangChain extraction chains.

Granite4:350m has 32k context window — no chunking needed for
meetings up to ~4 hours of transcript text.
"""
import asyncio
import logging
import os
import re
from pathlib import Path
from typing import Optional

import yaml

try:
    import nest_asyncio
    nest_asyncio.apply()          # safe to call multiple times
except ImportError:
    pass                          # only needed in threaded/Celery contexts

from intelligence.schemas import MeetingIntelligence, MeetingSummary
from intelligence.chains.summarize import summarize_meeting
from intelligence.chains.action_items import extract_action_items
from intelligence.chains.decisions import extract_decisions

logger = logging.getLogger(__name__)


# ── config loader with ${ENV_VAR} resolution ─────────────────────────────────

def _resolve_env(val):
    """Recursively resolve ${ENV_VAR} placeholders in config values."""
    if isinstance(val, str):
        return re.sub(
            r"\$\{(\w+)\}",
            lambda m: os.environ.get(m.group(1), ""),
            val,
        )
    if isinstance(val, dict):
        return {k: _resolve_env(v) for k, v in val.items()}
    if isinstance(val, list):
        return [_resolve_env(v) for v in val]
    return val


def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path, "r") as f:
        raw = yaml.safe_load(f)
    return _resolve_env(raw)


# ── pipeline ──────────────────────────────────────────────────────────────────

class IntelligencePipeline:
    """
    Run summarization, action-item extraction, and decision extraction
    in parallel using asyncio.gather().

    Granite4:350m context = 32 000 tokens.
    A 1-hour meeting transcript ≈ 6 000–10 000 tokens → fits comfortably.
    No chunking required.
    """

    def __init__(self, config_path: str = "config.yaml"):
        self.config = load_config(config_path)
        self.llm_config = self.config["llm"]
        self.llm = self._create_llm()

    def _create_llm(self):
        provider    = self.llm_config["provider"]
        model       = self.llm_config["model"]
        temperature = self.llm_config.get("temperature", 0.1)   # low = consistent JSON
        max_tokens  = self.llm_config.get("max_tokens", 8000)

        logger.info("Creating LLM: provider=%s  model=%s", provider, model)

        if provider == "ollama":
            from langchain_ollama import ChatOllama
            return ChatOllama(
                model=model,
                temperature=temperature,
                format="json",           # force JSON output mode
                num_ctx=32768,           # granite4:350m full context window
            )

        if provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            api_key = os.environ.get("ANTHROPIC_API_KEY", "")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not set")
            return ChatAnthropic(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=api_key,
            )

        if provider == "openai":
            from langchain_openai import ChatOpenAI
            api_key = os.environ.get("OPENAI_API_KEY", "")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set")
            return ChatOpenAI(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=api_key,
            )

        raise ValueError(f"Unsupported LLM provider: {provider!r}")

    async def process(self, transcript: str) -> MeetingIntelligence:
        if not transcript or not transcript.strip():
            logger.warning("Empty transcript — skipping LLM extraction")
            return MeetingIntelligence(
                summary=MeetingSummary(
                    title="Untitled Meeting",
                    summary="No speech detected in the recording.",
                    key_points=[],
                    participants=[],
                ),
                action_items=[],
                decisions=[],
                transcript=transcript,
            )

        logger.info("Running intelligence pipeline (granite4:350m, 32k ctx)…")

        # all three chains run in parallel — total latency = slowest chain
        summary, action_items, decisions = await asyncio.gather(
            summarize_meeting(self.llm, transcript),
            extract_action_items(self.llm, transcript),
            extract_decisions(self.llm, transcript),
        )

        logger.info(
            "Intelligence extraction complete: %d key points, "
            "%d action items, %d decisions",
            len(summary.key_points), len(action_items), len(decisions),
        )

        return MeetingIntelligence(
            summary=summary,
            action_items=action_items,
            decisions=decisions,
            transcript=transcript,
        )

    def process_sync(self, transcript: str) -> MeetingIntelligence:
        """Synchronous entry point — safe to call from any thread."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # inside an already-running loop (Jupyter, some Celery configs)
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                    future = ex.submit(asyncio.run, self.process(transcript))
                    return future.result()
            return loop.run_until_complete(self.process(transcript))
        except RuntimeError:
            return asyncio.run(self.process(transcript))