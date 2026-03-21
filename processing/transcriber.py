"""
Speech-to-text transcription.

Uses faster-whisper (CTranslate2 backend) for GPU-accelerated, high-accuracy
transcription. The 'medium' model with int8 quantization fits comfortably in
4GB VRAM while delivering near-large quality.
"""
import logging
import os
from pathlib import Path
from typing import Dict, List

import yaml

logger = logging.getLogger(__name__)


class Transcriber:
    """Transcribe audio using faster-whisper (CTranslate2 quantised)."""

    def __init__(self, config_path: str = "config.yaml"):
        self.model_size  = "medium"   # Excellent quality, ~1.4GB VRAM with int8
        self.device      = "auto"     # auto → CUDA if available, else CPU
        self.compute_type = "int8"    # int8 on GPU: fastest without quality loss
        self.stt_config  = {}

        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config = yaml.safe_load(f) or {}
                    self.stt_config = config.get("stt", {})
            except Exception as exc:
                logger.warning(f"Could not read config.yaml: {exc}")

        # Allow overrides from config.yaml
        if self.stt_config.get("model"):
            self.model_size = self.stt_config["model"]
        if self.stt_config.get("device"):
            self.device = self.stt_config["device"]
        if self.stt_config.get("compute_type"):
            self.compute_type = self.stt_config["compute_type"]

        self._language = self.stt_config.get("language", None)
        self.model = None
        self._load_model()

    def _load_model(self):
        from faster_whisper import WhisperModel  # lazy import
        logger.info(f"Loading faster-whisper model: {self.model_size} (device={self.device}, compute={self.compute_type})")
        print(f"⏳ Loading transcription model ({self.model_size})…")
        self.model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type,
        )
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

        kwargs: Dict = {
            "beam_size":    5,
            "best_of":      5,
            "vad_filter":   True,     # skip silence chunks → faster + cleaner
            "vad_parameters": {"min_silence_duration_ms": 500},
        }
        if self._language:
            kwargs["language"] = self._language

        raw_segments, info = self.model.transcribe(str(audio_path), **kwargs)

        # faster-whisper returns a generator — consume it
        segments: List[Dict] = []
        for seg in raw_segments:
            segments.append({
                "start": round(seg.start, 3),
                "end":   round(seg.end, 3),
                "text":  seg.text.strip(),
            })

        detected_lang = info.language
        full_text = " ".join(s["text"] for s in segments)

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