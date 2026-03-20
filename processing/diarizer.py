"""Speaker diarization using pyannote-audio."""
from pyannote.audio import Pipeline
from pathlib import Path
from typing import Dict, List
import os


class Diarizer:
    """Speaker diarization to identify who spoke when."""
    
    def __init__(self, hf_token: Optional[str] = None):
        """
        Initialize diarizer.
        
        Args:
            hf_token: HuggingFace token for pyannote models
        """
        self.hf_token = hf_token or os.getenv('HF_TOKEN')
        if not self.hf_token:
            raise ValueError("HuggingFace token required for pyannote. Set HF_TOKEN env var.")
        
        self.pipeline = None
        self._load_pipeline()
    
    def _load_pipeline(self):
        """Load pyannote diarization pipeline."""
        print("📥 Loading pyannote diarization pipeline...")
        
        self.pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=self.hf_token
        )
        
        print("✅ Diarization pipeline loaded")
    
    def diarize(
        self,
        audio_path: Path,
        min_speakers: Optional[int] = None,
        max_speakers: Optional[int] = None
    ) -> List[Dict]:
        """
        Perform speaker diarization.
        
        Args:
            audio_path: Path to audio file
            min_speakers: Minimum number of speakers
            max_speakers: Maximum number of speakers
            
        Returns:
            List of speaker segments with timestamps
        """
        print(f"👥 Diarizing speakers: {audio_path.name}")
        
        # Run diarization
        diarization = self.pipeline(
            str(audio_path),
            min_speakers=min_speakers,
            max_speakers=max_speakers
        )
        
        # Convert to list of segments
        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append({
                'speaker': speaker,
                'start': turn.start,
                'end': turn.end
            })
        
        num_speakers = len(set(seg['speaker'] for seg in segments))
        print(f"✅ Diarization complete: {num_speakers} speakers, {len(segments)} segments")
        
        return segments
    
    def merge_with_transcript(
        self,
        transcript: Dict,
        diarization: List[Dict]
    ) -> List[Dict]:
        """
        Merge diarization with transcript word timestamps.
        
        Args:
            transcript: Transcript with word timestamps from Whisper
            diarization: Speaker segments from pyannote
            
        Returns:
            Merged transcript with speaker labels
        """
        print("🔗 Merging transcript with speaker labels...")
        
        merged_segments = []
        
        for segment in transcript['segments']:
            # Find speaker for this segment based on timestamp overlap
            segment_start = segment['start']
            segment_end = segment['end']
            
            # Find the speaker with most overlap
            best_speaker = None
            max_overlap = 0
            
            for diar_seg in diarization:
                overlap_start = max(segment_start, diar_seg['start'])
                overlap_end = min(segment_end, diar_seg['end'])
                overlap = max(0, overlap_end - overlap_start)
                
                if overlap > max_overlap:
                    max_overlap = overlap
                    best_speaker = diar_seg['speaker']
            
            merged_segments.append({
                'speaker': best_speaker or 'UNKNOWN',
                'start': segment_start,
                'end': segment_end,
                'text': segment['text'],
                'words': segment.get('words', [])
            })
        
        print(f"✅ Merged {len(merged_segments)} segments with speaker labels")
        return merged_segments
