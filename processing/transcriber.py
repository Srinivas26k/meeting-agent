"""
Speech-to-text transcription.

Uses faster-whisper (CTranslate2 backend) for 4-6x faster inference
at the same accuracy as openai-whisper, with int8 CPU quantization.
Auto-selects the best model based on available hardware.
"""
import logging
import os
import platform
from pathlib import Path
from typing import Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


# ── hardware auto-detection ───────────────────────────────────────────────────

def _detect_device() -> tuple[str, str]:
    """Return (device, compute_type) based on available hardware."""
    try:
        import torch
        if torch.cuda.is_available():
            vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
            logger.info("CUDA detected: %.1f GB VRAM", vram_gb)
            compute = "float16" if vram_gb >= 4 else "int8"
            return "cuda", compute
    except ImportError:
        pass

    logger.info("No CUDA — running on CPU with int8 quantization")
    return "cpu", "int8"


def _detect_model(device: str) -> str:
    """Pick the best model that fits available RAM."""
    import psutil
    ram_gb = psutil.virtual_memory().available / 1e9

    if device == "cuda":
        return "large-v3-turbo"

    # CPU model tiers by available RAM
    if ram_gb >= 8:
        return "distil-large-v3"   # 756M params, 6x faster, within 1% WER
    elif ram_gb >= 4:
        return "small"
    elif ram_gb >= 2:
        return "base"
    else:
        return "tiny"


# ── Transcriber ───────────────────────────────────────────────────────────────

class Transcriber:
    """Transcribe audio using faster-whisper (CTranslate2 backend)."""

    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        self.stt_config = config.get("stt", {})
        self.model = None
        self._load_model()

    def _load_model(self):
        from faster_whisper import WhisperModel

        device, compute_type = _detect_device()

        # config.yaml can override auto-detection
        model_size = self.stt_config.get("model") or _detect_model(device)
        device     = self.stt_config.get("device", device)
        compute    = self.stt_config.get("compute_type", compute_type)

        logger.info(
            "Loading faster-whisper model: %s  device=%s  compute=%s",
            model_size, device, compute,
        )

        # num_workers=2 speeds up CPU inference on multi-core machines
        cpu_threads = min(os.cpu_count() or 4, 4)

        self.model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute,
            cpu_threads=cpu_threads,
            download_root=os.path.expanduser("~/.cache/faster-whisper"),
        )
        self._language = self.stt_config.get("language") or None
        self._word_ts  = self.stt_config.get("word_timestamps", True)

        logger.info("Model loaded: %s", model_size)

    def transcribe(self, audio_path: Path) -> Dict:
        """
        Transcribe audio file.

        Returns
        -------
        dict with keys:
            language  : str
            text      : str   (full concatenated transcript)
            segments  : list  (dicts with start/end/text/words)
        """
        logger.info("Transcribing: %s", audio_path.name)

        # faster-whisper transcribe() returns a generator + info object
        seg_generator, info = self.model.transcribe(
            str(audio_path),
            language=self._language,
            word_timestamps=self._word_ts,
            vad_filter=True,           # Silero VAD — skips silence automatically
            vad_parameters={
                "min_silence_duration_ms": 500,
                "speech_pad_ms": 200,
            },
            beam_size=5,
            best_of=5,
            temperature=0.0,           # greedy decoding → faster + deterministic
            condition_on_previous_text=True,
        )

        segments: List[Dict] = []
        full_text_parts: List[str] = []

        # consume the generator — this is where inference actually runs
        for seg in seg_generator:
            words = []
            if self._word_ts and hasattr(seg, "words") and seg.words:
                for w in seg.words:
                    words.append({
                        "word":        w.word,
                        "start":       round(w.start, 3),
                        "end":         round(w.end, 3),
                        "probability": round(w.probability, 4),
                    })

            segments.append({
                "start": round(seg.start, 3),
                "end":   round(seg.end, 3),
                "text":  seg.text.strip(),
                "words": words,
            })
            full_text_parts.append(seg.text.strip())

        detected_lang = info.language
        full_text     = " ".join(full_text_parts)

        logger.info(
            "Transcription complete: %d segments, language=%s",
            len(segments), detected_lang,
        )

        return {
            "language": detected_lang,
            "segments": segments,
            "text":     full_text,
        }

    def transcribe_to_text(self, audio_path: Path) -> str:
        """Convenience wrapper — returns only the full text string."""
        return self.transcribe(audio_path)["text"]