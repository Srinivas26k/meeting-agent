"""
Speech-to-text transcription.

Uses openai-whisper for reliable, highly-compatible transcription.
Uses the 'tiny' model by default to run smoothly on any device.
"""
import logging
import os
from pathlib import Path
from typing import Dict, List

import yaml
import whisper

logger = logging.getLogger(__name__)

class Transcriber:
    """Transcribe audio using openai-whisper."""

    def __init__(self, config_path: str = "config.yaml"):
        self.model_size = "tiny"
        self.stt_config = {}
        
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config = yaml.safe_load(f) or {}
                    self.stt_config = config.get("stt", {})
            except Exception as e:
                logger.warning(f"Could not read config.yaml: {e}")

        # Config override if present
        if self.stt_config.get("model"):
            self.model_size = self.stt_config["model"]

        self.model = None
        self._load_model()

    def _load_model(self):
        logger.info(f"Loading openai-whisper model: {self.model_size}")
        self.model = whisper.load_model(self.model_size)
        self._language = self.stt_config.get("language", None)
        logger.info(f"Model loaded: {self.model_size}")

    def transcribe(self, audio_path: Path) -> Dict:
        """
        Transcribe audio file.
        
        Returns
        -------
        dict with keys:
            language  : str
            text      : str   (full concatenated transcript)
            segments  : list  (dicts with start/end/text)
        """
        logger.info(f"Transcribing: {audio_path.name}")
        
        kwargs = {}
        if self._language:
            kwargs["language"] = self._language
            
        result = self.model.transcribe(str(audio_path), **kwargs)

        segments: List[Dict] = []
        for seg in result.get("segments", []):
            segments.append({
                "start": round(seg.get("start", 0.0), 3),
                "end":   round(seg.get("end", 0.0), 3),
                "text":  seg.get("text", "").strip(),
            })

        detected_lang = result.get("language", "")
        full_text = result.get("text", "").strip()

        logger.info(
            f"Transcription complete: {len(segments)} segments, language={detected_lang}"
        )

        return {
            "language": detected_lang,
            "segments": segments,
            "text":     full_text,
        }

    def transcribe_to_text(self, audio_path: Path) -> str:
        """Convenience wrapper — returns only the full text string."""
        return self.transcribe(audio_path)["text"]