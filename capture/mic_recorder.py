"""Live microphone recording using soundcard."""
import threading
import wave
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import soundcard as sc


class MicRecorder:
    """Record audio from microphone."""
    
    def __init__(self, sample_rate: int = 48000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.recording = []
        self.is_recording = False
        self.thread: Optional[threading.Thread] = None
        self._error: Optional[Exception] = None
        
        # Get default mic
        self.mic = self._resolve_mic()

    def _resolve_mic(self):
        try:
            return sc.default_microphone()
        except Exception:
            try:
                mics = sc.all_microphones(include_loopback=False)
                if mics:
                    return mics[0]
            except Exception:
                pass
        return None
    
    def _record_loop(self):
        if self.mic is None:
            self._error = RuntimeError("No input microphone device found.")
            self.is_recording = False
            return

        mic = self.mic
        assert mic is not None, "Microphone must not be None when starting record loop"
        try:
            with mic.recorder(samplerate=self.sample_rate, channels=self.channels) as recorder:
                while self.is_recording:
                    # Record 1 second chunks
                    data = recorder.record(numframes=self.sample_rate)
                    self.recording.append(data)
        except Exception as exc:
            self._error = exc
            self.is_recording = False

    def start(self):
        """Start recording from microphone."""
        if self.mic is None:
            raise RuntimeError(
                "Audio backend is available but no input microphone device found."
            )

        self.recording = []
        self._error = None
        self.is_recording = True
        thread = threading.Thread(target=self._record_loop, daemon=True)
        self.thread = thread
        thread.start()
        print(f"🎤 Recording started (sample rate: {self.sample_rate}Hz)")
    
    def stop(self, output_path: Optional[str] = None) -> Path:
        """
        Stop recording and save to file.
        """
        self.is_recording = False
        thread = self.thread
        if thread is not None:
            thread.join(timeout=5)

        if self._error is not None:
            raise RuntimeError(f"Microphone capture failed: {self._error}")
        
        if not self.recording:
            raise ValueError("No audio data recorded")
        
        # Concatenate all recorded chunks
        audio_data = np.concatenate(self.recording, axis=0)
        
        # Generate output path if not provided
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path_str = f"recording_mic_{timestamp}.wav"
        else:
            output_path_str = output_path
        
        out_path = Path(output_path_str)
        
        # Save as WAV file
        channels = audio_data.shape[1] if len(audio_data.shape) > 1 else self.channels
        with wave.open(str(out_path), 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.sample_rate)
            # Convert float to int16 safely without overflow static
            audio_int16 = (np.clip(audio_data, -1.0, 1.0) * 32767).astype(np.int16)
            wf.writeframes(audio_int16.tobytes())
        
        print(f"✅ Recording saved to {out_path}")
        return out_path
    
    def pause(self):
        self.is_recording = False
        print("⏸️  Recording paused")
    
    def resume(self):
        self.is_recording = True
        thread = threading.Thread(target=self._record_loop, daemon=True)
        self.thread = thread
        thread.start()
        print("▶️  Recording resumed")
