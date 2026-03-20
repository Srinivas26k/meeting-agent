"""Celery tasks for background processing."""
from celery import Celery
from pathlib import Path
import yaml

# Load config
with open("config.yaml", 'r') as f:
    config = yaml.safe_load(f)

# Initialize Celery
celery_app = Celery(
    'meeting_agent',
    broker=config['celery']['broker_url'],
    backend=config['celery']['result_backend']
)


@celery_app.task(bind=True)
def process_meeting_task(self, file_path: str, skip_diarization: bool = False):
    """
    Background task to process a meeting recording.
    
    Args:
        file_path: Path to the audio/video file
        skip_diarization: Whether to skip speaker diarization
        
    Returns:
        Dictionary with meeting intelligence data
    """
    from capture.file_loader import FileLoader
    from processing.preprocessor import AudioPreprocessor
    from processing.transcriber import Transcriber
    from processing.diarizer import Diarizer
    from intelligence.pipeline import IntelligencePipeline
    from storage.database import Database
    
    try:
        # Update task state
        self.update_state(state='PROCESSING', meta={'step': 'loading', 'progress': 0.1})
        
        # Load file
        file_path_obj = FileLoader.load(file_path)
        
        # Preprocess
        self.update_state(state='PROCESSING', meta={'step': 'preprocessing', 'progress': 0.2})
        preprocessor = AudioPreprocessor()
        processed_audio = preprocessor.process(file_path_obj)
        
        # Transcribe
        self.update_state(state='PROCESSING', meta={'step': 'transcription', 'progress': 0.3})
        transcriber = Transcriber()
        transcript = transcriber.transcribe(processed_audio)
        
        # Diarization
        if not skip_diarization:
            self.update_state(state='PROCESSING', meta={'step': 'diarization', 'progress': 0.6})
            try:
                diarizer = Diarizer()
                diarization = diarizer.diarize(processed_audio)
                merged_transcript = diarizer.merge_with_transcript(transcript, diarization)
                formatted_text = "\n\n".join([
                    f"{seg['speaker']}: {seg['text']}"
                    for seg in merged_transcript
                ])
            except Exception as e:
                print(f"Diarization failed: {e}")
                formatted_text = transcript['text']
        else:
            formatted_text = transcript['text']
        
        # Intelligence extraction
        self.update_state(state='PROCESSING', meta={'step': 'intelligence', 'progress': 0.8})
        pipeline = IntelligencePipeline()
        intelligence = pipeline.process_sync(formatted_text)
        
        # Save to database
        self.update_state(state='PROCESSING', meta={'step': 'saving', 'progress': 0.9})
        db = Database()
        meeting_data = {
            'title': intelligence.summary.title,
            'participants': intelligence.summary.participants,
            'duration_minutes': intelligence.summary.duration_minutes,
            'audio_file_path': str(file_path_obj),
            'transcript': intelligence.transcript,
            'summary': intelligence.summary.summary,
            'key_points': intelligence.summary.key_points,
            'action_items': [item.dict() for item in intelligence.action_items],
            'decisions': [dec.dict() for dec in intelligence.decisions]
        }
        meeting = db.create_meeting(meeting_data)
        
        return {
            'status': 'completed',
            'meeting_id': meeting.id,
            'title': intelligence.summary.title,
            'action_items_count': len(intelligence.action_items),
            'decisions_count': len(intelligence.decisions)
        }
        
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise
