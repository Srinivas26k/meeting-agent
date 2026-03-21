"""Live microphone recording via ffmpeg + PulseAudio.

Uses ffmpeg -f pulse (same path as screen recorder) for clean, studio-quality
capture without Python audio-driver float32 artifacts.
"""
import os
import signal
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional


# ── helpers ──────────────────────────────────────────────────────────────────

def _pulse_default_source() -> str:
    """Return the PulseAudio default source name, falling back to 'default'."""
    try:
        out = subprocess.check_output(
            ["pactl", "get-default-source"], stderr=subprocess.DEVNULL, text=True
        ).strip()
        return out or "default"
    except Exception:
        return "default"


# ── recorder ─────────────────────────────────────────────────────────────────

class MicRecorder:
    """Record audio from the default microphone using ffmpeg PulseAudio capture.

    Uses the same ffmpeg subprocess approach as ScreenRecorder, bypassing
    soundcard's float32 DC-bias issues on Linux drivers.
    """

    def __init__(self, sample_rate: int = 44100, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self._process: Optional[subprocess.Popen] = None
        self._output_path: Optional[Path] = None

    # ── internal ─────────────────────────────────────────────────────────────

    def _build_command(self, output_path: str) -> list:
        source = _pulse_default_source()
        return [
            "ffmpeg",
            "-nostdin",
            "-f",      "pulse",
            "-i",      source,
            "-ar",     str(self.sample_rate),
            "-ac",     str(self.channels),
            "-acodec", "pcm_s16le",   # uncompressed 16-bit LE (lossless WAV)
            # High-pass @80Hz removes mic rumble; mild compressor levels voice
            "-af",     "highpass=f=80,acompressor=threshold=0.1:ratio=2:attack=5:release=50",
            "-y",
            output_path,
        ]

    # ── public API ────────────────────────────────────────────────────────────

    def start(self, output_path: Optional[str] = None) -> Path:
        """Start recording. Returns the path the file will be saved to."""
        if self._process is not None:
            raise RuntimeError("Recording already in progress")

        if output_path is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"recording_mic_{ts}.wav"

        self._output_path = Path(output_path)
        cmd = self._build_command(str(self._output_path))

        self._process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )

        # Give ffmpeg a moment to open the device; fail fast on misconfiguration
        time.sleep(0.4)
        if self._process.poll() is not None:
            _, stderr = self._process.communicate(timeout=2)
            self._process = None
            msg = stderr.decode(errors="ignore").strip()
            raise RuntimeError(f"Mic recording failed to start: {msg}")

        print(f"🎤 Recording started (sample rate: {self.sample_rate}Hz, source: {_pulse_default_source()})")
        return self._output_path

    def stop(self, output_path: Optional[str] = None) -> Path:
        """Stop recording, flush WAV, and return the saved file path."""
        proc = self._process
        if proc is None:
            raise RuntimeError("No recording in progress")

        # SIGINT tells ffmpeg to flush correctly and write a valid WAV header
        proc.send_signal(signal.SIGINT)
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()

        self._process = None
        out = self._output_path

        if output_path is not None:
            dest = Path(output_path)
            if out and out.exists():
                out.rename(dest)
            out = dest

        self._output_path = None

        if out is None or not out.exists():
            raise RuntimeError("Recording file was not created by ffmpeg")

        print(f"✅ Recording saved to {out}")
        return out

    # ── compat shims ──────────────────────────────────────────────────────────

    def pause(self):
        print("⏸️  Pause requested — ffmpeg backend does not support pause (recording continues)")

    def resume(self):
        print("▶️  Resume requested — recording was never paused")
