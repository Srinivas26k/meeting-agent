"""Live microphone recording using sounddevice."""
import sounddevice as sd
import numpy as np
from pathlib import Path
import wave
from typing import Optional
from datetime import datetime


class MicRecorder:
    """Record audio from microphone."""
    
    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.recording = []
        self.is_recording = False
        self.stream: Optional[sd.InputStream] = None
    
    def _audio_callback(self, indata, frames, time, status):
        """Callback for audio stream."""
        if status:
            print(f"Status: {status}")
        if self.is_recording:
            self.recording.append(indata.copy())
    
    def start(self):
        """Start recording from microphone."""
        self.recording = []
        self.is_recording = True
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            callback=self._audio_callback,
            dtype=np.float32
        )
        self.stream.start()
        print(f"🎤 Recording started (sample rate: {self.sample_rate}Hz)")
    
    def stop(self, output_path: Optional[str] = None) -> Path:
        """
        Stop recording and save to file.
        
        Args:
            output_path: Path to save the recording. If None, auto-generates filename.
            
        Returns:
            Path to the saved recording
        """
        self.is_recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
        
        if not self.recording:
            raise ValueError("No audio data recorded")
        
        # Concatenate all recorded chunks
        audio_data = np.concatenate(self.recording, axis=0)
        
        # Generate output path if not provided
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"recording_mic_{timestamp}.wav"
        
        output_path = Path(output_path)
        
        # Save as WAV file
        with wave.open(str(output_path), 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.sample_rate)
            # Convert float32 to int16
            audio_int16 = (audio_data * 32767).astype(np.int16)
            wf.writeframes(audio_int16.tobytes())
        
        print(f"✅ Recording saved to {output_path}")
        return output_path
    
    def pause(self):
        """Pause recording."""
        self.is_recording = False
        print("⏸️  Recording paused")
    
    def resume(self):
        """Resume recording."""
        self.is_recording = True
        print("▶️  Recording resumed")
