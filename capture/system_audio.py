"""System audio loopback capture using soundcard."""
import soundcard as sc
import numpy as np
from pathlib import Path
from typing import Optional
from datetime import datetime
import wave
import threading


class SystemAudioRecorder:
    """Record system audio (loopback) from speakers."""
    
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.recording = []
        self.is_recording = False
        self.thread: Optional[threading.Thread] = None
        
        # Get default loopback device
        try:
            self.loopback = sc.default_speaker()
        except Exception as e:
            print(f"Warning: Could not get default speaker for loopback: {e}")
            self.loopback = None
    
    def _record_loop(self):
        """Recording loop running in separate thread."""
        if self.loopback is None:
            print("Error: No loopback device available")
            return
        
        with self.loopback.recorder(samplerate=self.sample_rate) as mic:
            while self.is_recording:
                data = mic.record(numframes=self.sample_rate)  # 1 second chunks
                self.recording.append(data)
    
    def start(self):
        """Start recording system audio."""
        if self.loopback is None:
            raise RuntimeError("No loopback device available")
        
        self.recording = []
        self.is_recording = True
        self.thread = threading.Thread(target=self._record_loop, daemon=True)
        self.thread.start()
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
        if self.thread:
            self.thread.join(timeout=5)
        
        if not self.recording:
            raise ValueError("No audio data recorded")
        
        # Concatenate all recorded chunks
        audio_data = np.concatenate(self.recording, axis=0)
        
        # Generate output path if not provided
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"recording_system_{timestamp}.wav"
        
        output_path = Path(output_path)
        
        # Save as WAV file
        channels = audio_data.shape[1] if len(audio_data.shape) > 1 else 1
        with wave.open(str(output_path), 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.sample_rate)
            # Convert float to int16
            audio_int16 = (audio_data * 32767).astype(np.int16)
            wf.writeframes(audio_int16.tobytes())
        
        print(f"✅ System audio saved to {output_path}")
        return output_path
