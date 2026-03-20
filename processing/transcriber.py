"""Speech-to-text transcription using openai-whisper."""
import whisper
from pathlib import Path
from typing import Dict, Optional
import yaml


class Transcriber:
    """Transcribe audio using openai-whisper."""

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize transcriber with config."""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        self.stt_config = config['stt']
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load the Whisper model."""
        model_name = self.stt_config.get('model', 'tiny')
        print(f"📥 Loading Whisper model: {model_name}")
        self.model = whisper.load_model(model_name)
        print("✅ Model loaded successfully")

    def transcribe(self, audio_path: Path) -> Dict:
        """
        Transcribe audio file.

        Args:
            audio_path: Path to audio file

        Returns:
            Dictionary with transcript text and segments
        """
        print(f"🎙️  Transcribing: {audio_path.name}")

        language = self.stt_config.get('language') or None

        result = self.model.transcribe(
            str(audio_path),
            language=language,
            word_timestamps=self.stt_config.get('word_timestamps', False),
            verbose=False,
        )

        segments = []
        for seg in result.get('segments', []):
            segment_data = {
                'start': seg['start'],
                'end': seg['end'],
                'text': seg['text'].strip(),
                'words': []
            }
            # word timestamps only available when word_timestamps=True
            for w in seg.get('words', []):
                segment_data['words'].append({
                    'word': w['word'],
                    'start': w['start'],
                    'end': w['end'],
                    'probability': w.get('probability', 1.0)
                })
            segments.append(segment_data)

        detected_language = result.get('language', 'unknown')
        print(f"   Detected language: {detected_language}")
        print(f"✅ Transcription complete: {len(segments)} segments")

        return {
            'language': detected_language,
            'segments': segments,
            'text': result['text'].strip()
        }

    def transcribe_to_text(self, audio_path: Path) -> str:
        """Simple transcription returning only text."""
        return self.transcribe(audio_path)['text']
