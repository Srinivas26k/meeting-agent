"""System audio loopback capture using soundcard.

This module is intentionally defensive because loopback capture support varies
by OS/driver stack:
* Windows (WASAPI): usually supported
* macOS / Linux: may require virtual loopback devices (BlackHole/Pulse monitor)
"""
import threading
import wave
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import soundcard as sc


class SystemAudioRecorder:
    """Record system audio (loopback) from speakers."""
    
    def __init__(self, sample_rate: int = 48000):
        self.sample_rate = sample_rate
        self.recording = []
        self.is_recording = False
        self.thread: Optional[threading.Thread] = None
        self._error: Optional[Exception] = None
        
        # Get default loopback device
        self.loopback = self._resolve_loopback()

    def _resolve_loopback(self):
        """Resolve a recorder-capable loopback source across platforms."""
        try:
            default_speaker = sc.default_speaker()
        except Exception:
            default_speaker = None

        # Best option: a microphone representing a loopback endpoint.
        try:
            loopback_mics = sc.all_microphones(include_loopback=True)
        except Exception:
            loopback_mics = []

        if default_speaker is not None and loopback_mics:
            for mic in loopback_mics:
                mic_name = getattr(mic, "name", "")
                spk_name = getattr(default_speaker, "name", "")
                if spk_name and spk_name in mic_name:
                    return mic

        if loopback_mics:
            return loopback_mics[0]

        # Fallback for APIs that expose recorder directly on speaker object.
        if default_speaker is not None and hasattr(default_speaker, "recorder"):
            return default_speaker

        return None
    
    def _record_loop(self):
        """Recording loop running in separate thread."""
        loopback = self.loopback
        if loopback is None:
            print("Error: No loopback device available")
            return

        try:
            with loopback.recorder(samplerate=self.sample_rate) as mic:
                while self.is_recording:
                    data = mic.record(numframes=self.sample_rate)  # 1 second chunks
                    self.recording.append(data)
        except Exception as exc:
            self._error = exc
            self.is_recording = False
    
    def start(self):
        """Start recording system audio."""
        if self.loopback is None:
            raise RuntimeError(
                "System loopback audio is not available on this device. "
                "On macOS/Linux, install/configure a loopback device (e.g., "
                "BlackHole or PulseAudio monitor)."
            )

        self.recording = []
        self._error = None
        self.is_recording = True
        thread = threading.Thread(target=self._record_loop, daemon=True)
        self.thread = thread
        thread.start()
        print(f"🔊 System audio recording started (sample rate: {self.sample_rate}Hz)")
    
    def stop(self, output_path: Optional[str] = None) -> Path:
        """
        Stop recording and save to file.
        
        Args:
            output_path: Path to save the recording. If None, auto-generates filename.
            
        Returns:
            Path to the saved recording
        """
        self.is_recording = False
        thread = self.thread
        if thread is not None:
            thread.join(timeout=5)

        if self._error is not None:
            raise RuntimeError(f"System audio capture failed: {self._error}")
        
        if not self.recording:
            raise ValueError("No audio data recorded")
        
        # Concatenate all recorded chunks
        audio_data = np.concatenate(self.recording, axis=0)
        
        # Generate output path if not provided
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path_str = f"recording_system_{timestamp}.wav"
        else:
            output_path_str = output_path
        
        out_path = Path(output_path_str)
        
        # Save as WAV file
        channels = audio_data.shape[1] if len(audio_data.shape) > 1 else 1
        with wave.open(str(out_path), 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.sample_rate)
            # Convert float to int16 safely without overflow static
            audio_int16 = (np.clip(audio_data, -1.0, 1.0) * 32767).astype(np.int16)
            wf.writeframes(audio_int16.tobytes())
        
        print(f"✅ System audio saved to {out_path}")
        return out_path
