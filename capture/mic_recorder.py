"""Live microphone recording via ffmpeg + ALSA (Linux).

Uses ffmpeg -f alsa to write directly to the kernel audio driver,
bypassing the PulseAudio software mixer layer for the cleanest
possible capture path on Linux.

Falls back to PulseAudio (-f pulse) if ALSA is unavailable.
"""
import os
import signal
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional


# ── ALSA device detection ─────────────────────────────────────────────────────

def _detect_alsa_mic() -> Optional[str]:
    """
    Parse `arecord -l` to find the first capture device.
    Returns an ALSA device string like 'hw:1,0', or None if not found.
    """
    try:
        out = subprocess.check_output(
            ["arecord", "-l"], stderr=subprocess.DEVNULL, text=True
        )
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("card "):
                # Example: "card 1: Generic [HD-Audio Generic], device 0: ..."
                parts = line.split(":")
                card_num = parts[0].split()[1]
                dev_part = parts[1].split(",")[1].strip()  # "device 0: ..."
                dev_num  = dev_part.split()[1]
                return f"hw:{card_num},{dev_num}"
    except Exception:
        pass
    return None


def _best_audio_source():
    """
    Return (ffmpeg_format, device) for the cleanest available audio source.
    Prefers ALSA (direct kernel), falls back to PulseAudio.
    """
    alsa_dev = _detect_alsa_mic()
    if alsa_dev:
        # Verify ALSA device actually opens without error
        try:
            test = subprocess.run(
                ["ffmpeg", "-f", "alsa", "-i", alsa_dev, "-t", "0.1",
                 "-f", "null", "-"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=3,
            )
            if test.returncode == 0 or test.returncode == 255:
                return "alsa", alsa_dev
        except Exception:
            pass

    # Fallback: PulseAudio
    try:
        out = subprocess.check_output(
            ["pactl", "get-default-source"], stderr=subprocess.DEVNULL, text=True
        ).strip()
        return "pulse", out or "default"
    except Exception:
        return "pulse", "default"


# ── recorder ─────────────────────────────────────────────────────────────────

class MicRecorder:
    """Record audio using ffmpeg ALSA (direct kernel) or PulseAudio fallback.

    ALSA bypasses the PulseAudio software mixer so there are no extra
    resampling or mixing artefacts. The ALC285 chip's inherent DC bias is
    then removed by the AudioPreprocessor before transcription.
    """

    def __init__(self, sample_rate: int = 44100, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels    = channels
        self._fmt, self._src = _best_audio_source()
        self._process: Optional[subprocess.Popen] = None
        self._output_path: Optional[Path] = None

    # ── internal ─────────────────────────────────────────────────────────────

    def _build_command(self, output_path: str) -> list:
        cmd = [
            "ffmpeg",
            "-nostdin",
            "-f",      self._fmt,
            "-i",      self._src,
            "-ar",     str(self.sample_rate),
            "-ac",     str(self.channels),
            "-acodec", "pcm_s16le",   # uncompressed 16-bit — no lossy artefacts
        ]

        if self._fmt == "alsa":
            # High-pass @80Hz removes sub-bass rumble from the ALC285 capsule;
            # gentle compressor keeps voice consistent without boosting noise floor.
            cmd += ["-af", "highpass=f=80,acompressor=threshold=0.1:ratio=2:attack=5:release=50"]
        else:
            # PulseAudio path — same filters still help
            cmd += ["-af", "highpass=f=80,acompressor=threshold=0.1:ratio=2:attack=5:release=50"]

        cmd += ["-y", output_path]
        return cmd

    # ── public API ────────────────────────────────────────────────────────────

    def start(self, output_path: Optional[str] = None) -> Path:
        """Start recording. Returns the path the WAV will be written to."""
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

        time.sleep(0.4)
        if self._process.poll() is not None:
            _, stderr = self._process.communicate(timeout=2)
            self._process = None
            msg = stderr.decode(errors="ignore").strip()
            raise RuntimeError(f"Mic recording failed to start: {msg}")

        backend = f"ALSA ({self._src})" if self._fmt == "alsa" else f"PulseAudio ({self._src})"
        print(f"🎤 Recording started (sample rate: {self.sample_rate}Hz, backend: {backend})")
        return self._output_path

    def stop(self, output_path: Optional[str] = None) -> Path:
        """Stop recording, flush WAV header, return the saved file path."""
        proc = self._process
        if proc is None:
            raise RuntimeError("No recording in progress")

        # SIGINT → ffmpeg flushes the RIFF header properly
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
            raise RuntimeError("Recording file was not created")

        print(f"✅ Recording saved to {out}")
        return out

    def pause(self):
        print("⏸️  Pause not supported by ffmpeg backend — recording continues")

    def resume(self):
        print("▶️  Recording was never paused")
