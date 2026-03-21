"""Audio preprocessing using ffmpeg."""
import ffmpeg
from pathlib import Path
from typing import Optional


class AudioPreprocessor:
    """Preprocess audio files for STT."""
    
    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
    
    def process(
        self,
        input_path: Path,
        output_path: Optional[Path] = None,
        normalize: bool = True
    ) -> Path:
        """
        Preprocess audio file: extract audio, resample, normalize.
        
        Args:
            input_path: Input audio/video file
            output_path: Output audio file. If None, auto-generates.
            normalize: Whether to normalize audio levels
            
        Returns:
            Path to processed audio file
        """
        if output_path is None:
            output_path = input_path.parent / f"{input_path.stem}_processed.wav"
        
        print(f"🔧 Preprocessing audio: {input_path.name}")
        
        # Build ffmpeg command: extract audio, resample to 16kHz mono
        stream = ffmpeg.input(str(input_path))
        stream = stream.audio

        # Apply normalization if requested (skip loudnorm — requires 2-pass)
        # Use simpler volume normalization instead
        if normalize:
            stream = stream.filter('acompressor')

        stream = ffmpeg.output(
            stream,
            str(output_path),
            acodec='pcm_s16le',
            ac=self.channels,
            ar=self.sample_rate,
            loglevel='error'
        )

        ffmpeg.run(stream, overwrite_output=True, quiet=True)
        
        print(f"✅ Preprocessed audio saved: {output_path.name}")
        return output_path
    
    def extract_audio_only(self, input_path: Path, output_path: Optional[Path] = None) -> Path:
        """Extract audio from video file."""
        if output_path is None:
            output_path = input_path.parent / f"{input_path.stem}_audio.wav"
        
        stream = ffmpeg.input(str(input_path))
        stream = ffmpeg.output(
            stream.audio,
            str(output_path),
            acodec='pcm_s16le',
            ac=self.channels,
            ar=self.sample_rate,
            loglevel='error'
        )
        
        ffmpeg.run(stream, overwrite_output=True, quiet=True)
        return output_path
