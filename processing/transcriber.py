"""Speech-to-text transcription using faster-whisper."""
from faster_whisper import WhisperModel
from pathlib import Path
from typing import List, Dict, Optional
import yaml


class Transcriber:
    """Transcribe audio using faster-whisper."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize transcriber with config."""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        self.stt_config = config['stt']
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the Whisper model."""
        print(f"📥 Loading Whisper model: {self.stt_config['model']}")
        
        self.model = WhisperModel(
            self.stt_config['model'],
            device=self.stt_config['device'],
            compute_type=self.stt_config['compute_type']
        )
        
        print(f"✅ Model loaded successfully")
    
    def transcribe(self, audio_path: Path) -> Dict:
        """
        Transcribe audio file.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary with transcript and word-level timestamps
        """
        print(f"🎙️  Transcribing: {audio_path.name}")
        
        segments, info = self.model.transcribe(
            str(audio_path),
            language=self.stt_config.get('language'),
            vad_filter=self.stt_config.get('vad_filter', True),
            word_timestamps=self.stt_config.get('word_timestamps', True)
        )
        
        print(f"   Detected language: {info.language} (probability: {info.language_probability:.2f})")
        
        # Process segments
        transcript_segments = []
        full_text = []
        
        for segment in segments:
            segment_data = {
                'start': segment.start,
                'end': segment.end,
                'text': segment.text.strip(),
                'words': []
            }
            
            # Add word-level timestamps if available
            if hasattr(segment, 'words') and segment.words:
                for word in segment.words:
                    segment_data['words'].append({
                        'word': word.word,
                        'start': word.start,
                        'end': word.end,
                        'probability': word.probability
                    })
            
            transcript_segments.append(segment_data)
            full_text.append(segment.text.strip())
        
        result = {
            'language': info.language,
            'language_probability': info.language_probability,
            'duration': info.duration,
            'segments': transcript_segments,
            'text': ' '.join(full_text)
        }
        
        print(f"✅ Transcription complete: {len(transcript_segments)} segments")
        return result
    
    def transcribe_to_text(self, audio_path: Path) -> str:
        """Simple transcription returning only text."""
        result = self.transcribe(audio_path)
        return result['text']
