"""Screen recording with audio using ffmpeg."""
import subprocess
import platform
from pathlib import Path
from typing import Optional
from datetime import datetime
import signal


class ScreenRecorder:
    """Record screen with audio using ffmpeg."""
    
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.output_path: Optional[Path] = None
    
    def _get_ffmpeg_command(self, output_path: str) -> list:
        """Generate platform-specific ffmpeg command."""
        system = platform.system()
        
        if system == "Windows":
            # Windows: gdigrab for screen, dshow for audio
            return [
                'ffmpeg',
                '-f', 'gdigrab',
                '-framerate', '30',
                '-i', 'desktop',
                '-f', 'dshow',
                '-i', 'audio=Microphone',
                '-c:v', 'libx264',
                '-preset', 'ultrafast',
                '-c:a', 'aac',
                '-y',
                output_path
            ]
        elif system == "Darwin":  # macOS
            # macOS: avfoundation
            return [
                'ffmpeg',
                '-f', 'avfoundation',
                '-framerate', '30',
                '-i', '1:0',  # Screen 1, Audio device 0
                '-c:v', 'libx264',
                '-preset', 'ultrafast',
                '-c:a', 'aac',
                '-y',
                output_path
            ]
        else:  # Linux
            # Linux: x11grab for screen, pulse for audio
            return [
                'ffmpeg',
                '-f', 'x11grab',
                '-framerate', '30',
                '-i', ':0.0',
                '-f', 'pulse',
                '-i', 'default',
                '-c:v', 'libx264',
                '-preset', 'ultrafast',
                '-c:a', 'aac',
                '-y',
                output_path
            ]
    
    def start(self, output_path: Optional[str] = None) -> Path:
        """
        Start screen recording.
        
        Args:
            output_path: Path to save the recording. If None, auto-generates filename.
            
        Returns:
            Path where recording will be saved
        """
        if self.process is not None:
            raise RuntimeError("Recording already in progress")
        
        # Generate output path if not provided
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"recording_screen_{timestamp}.mp4"
        
        self.output_path = Path(output_path)
        
        # Start ffmpeg process
        cmd = self._get_ffmpeg_command(str(self.output_path))
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        print(f"🎬 Screen recording started: {self.output_path}")
        return self.output_path
    
    def stop(self) -> Path:
        """
        Stop screen recording.
        
        Returns:
            Path to the saved recording
        """
        if self.process is None:
            raise RuntimeError("No recording in progress")
        
        # Send SIGINT to gracefully stop ffmpeg
        self.process.send_signal(signal.SIGINT)
        self.process.wait(timeout=10)
        
        print(f"✅ Screen recording saved to {self.output_path}")
        
        output = self.output_path
        self.process = None
        self.output_path = None
        
        return output
