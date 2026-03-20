"""File loader for audio/video meeting recordings."""
import os
from pathlib import Path
from typing import Optional


SUPPORTED_FORMATS = {'.mp4', '.mp3', '.wav', '.webm', '.m4a', '.ogg', '.flac'}


class FileLoader:
    """Load and validate audio/video files."""
    
    @staticmethod
    def load(file_path: str) -> Path:
        """
        Load and validate a meeting recording file.
        
        Args:
            file_path: Path to the audio/video file
            
        Returns:
            Path object of the validated file
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is not supported
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        if path.suffix.lower() not in SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported format: {path.suffix}. "
                f"Supported formats: {', '.join(SUPPORTED_FORMATS)}"
            )
        
        return path
    
    @staticmethod
    def get_file_info(file_path: Path) -> dict:
        """Get basic file information."""
        stat = file_path.stat()
        return {
            'name': file_path.name,
            'size_mb': stat.st_size / (1024 * 1024),
            'format': file_path.suffix,
            'path': str(file_path.absolute())
        }
