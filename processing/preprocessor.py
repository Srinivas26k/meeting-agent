"""Audio preprocessing using ffmpeg + noisereduce.

Pipeline:
  1. ffmpeg: extract audio from any source, downsample to 16kHz mono (Whisper format)
  2. noisereduce: spectral-gating noise suppression on the 16kHz signal
  3. Write final clean WAV
"""
import wave
from pathlib import Path
from typing import Optional

import ffmpeg
import numpy as np
import noisereduce as nr


class AudioPreprocessor:
    """Preprocess audio files for STT."""

    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels

    def process(
        self,
        input_path: Path,
        output_path: Optional[Path] = None,
        normalize: bool = True,
    ) -> Path:
        """
        Preprocess audio file: extract → resample → denoise → save.

        Steps:
          1. ffmpeg extracts & resamples to 16kHz mono PCM
          2. noisereduce removes stationary noise (hiss, hum, driver buzz)
          3. Peak normalise to 90% so Whisper gets consistent input levels
        """
        if output_path is None:
            output_path = input_path.parent / f"{input_path.stem}_processed.wav"

        print(f"🔧 Preprocessing audio: {input_path.name}")

        # ── Short-circuit: skip re-processing already-processed WAV files ─────
        # If file is already a 16kHz mono WAV, just copy and return — no need
        # to run noisereduce on already-clean audio (avoids _processed_processed).
        if input_path.suffix.lower() == ".wav":
            try:
                import wave as _wave
                with _wave.open(str(input_path), "rb") as _wf:
                    if _wf.getframerate() == self.sample_rate and _wf.getnchannels() == self.channels:
                        import shutil
                        if output_path != input_path:
                            shutil.copy2(input_path, output_path)
                        print(f"✅ Preprocessed audio saved: {output_path.name}")
                        return output_path
            except Exception:
                pass  # fall through to full preprocessing

        # ── Step 1: ffmpeg extract + resample to 16kHz mono ──────────────────
        tmp_raw = output_path.parent / f"_tmp_{output_path.stem}.wav"
        stream = ffmpeg.input(str(input_path)).audio
        stream = ffmpeg.output(
            stream,
            str(tmp_raw),
            acodec="pcm_s16le",
            ac=self.channels,
            ar=self.sample_rate,
            loglevel="error",
        )
        ffmpeg.run(stream, overwrite_output=True, quiet=True)

        # ── Step 2: load raw PCM, apply noisereduce ───────────────────────────
        with wave.open(str(tmp_raw), "rb") as wf:
            frames = wf.readframes(wf.getnframes())
            sr = wf.getframerate()

        audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32767.0

        # Spectral gating noise reduction — uses first 0.5s as noise profile
        # prop_decrease=0.85 → aggressive: removes 85% of identified noise energy
        audio_clean = nr.reduce_noise(
            y=audio,
            sr=sr,
            stationary=False,       # handles changing background (AC hum, traffic)
            prop_decrease=0.85,
            time_mask_smooth_ms=50,
            freq_mask_smooth_hz=500,
        )

        # ── Step 3: peak normalise to 90% full scale ─────────────────────────
        if normalize:
            peak = np.abs(audio_clean).max()
            if peak > 0.01:
                audio_clean = audio_clean / peak * 0.90

        # ── Step 4: save clean WAV ────────────────────────────────────────────
        audio_int16 = (np.clip(audio_clean, -1.0, 1.0) * 32767).astype(np.int16)
        with wave.open(str(output_path), "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_int16.tobytes())

        # Cleanup temp file
        tmp_raw.unlink(missing_ok=True)

        print(f"✅ Preprocessed audio saved: {output_path.name}")
        return output_path

    def extract_audio_only(self, input_path: Path, output_path: Optional[Path] = None) -> Path:
        """Extract audio from video file (no denoising — raw extraction only)."""
        if output_path is None:
            output_path = input_path.parent / f"{input_path.stem}_audio.wav"

        stream = ffmpeg.input(str(input_path))
        stream = ffmpeg.output(
            stream.audio,
            str(output_path),
            acodec="pcm_s16le",
            ac=self.channels,
            ar=self.sample_rate,
            loglevel="error",
        )
        ffmpeg.run(stream, overwrite_output=True, quiet=True)
        return output_path
