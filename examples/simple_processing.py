"""Simple example of processing a meeting recording."""
from pathlib import Path
from capture.file_loader import FileLoader
from processing.preprocessor import AudioPreprocessor
from processing.transcriber import Transcriber
from intelligence.pipeline import IntelligencePipeline
from storage.database import Database


def process_meeting(file_path: str):
    """Process a meeting recording end-to-end."""
    print(f"Processing: {file_path}\n")
    
    # 1. Load and validate file
    print("1️⃣  Loading file...")
    file_path_obj = FileLoader.load(file_path)
    info = FileLoader.get_file_info(file_path_obj)
    print(f"   ✅ {info['name']} ({info['size_mb']:.1f} MB)\n")
    
    # 2. Preprocess audio
    print("2️⃣  Preprocessing audio...")
    preprocessor = AudioPreprocessor()
    processed_audio = preprocessor.process(file_path_obj)
    print()
    
    # 3. Transcribe
    print("3️⃣  Transcribing...")
    transcriber = Transcriber()
    transcript = transcriber.transcribe(processed_audio)
    print(f"   ✅ Transcribed {len(transcript['segments'])} segments")
    print(f"   📝 Preview: {transcript['text'][:200]}...\n")
    
    # 4. Extract intelligence
    print("4️⃣  Extracting intelligence...")
    pipeline = IntelligencePipeline()
    intelligence = pipeline.process_sync(transcript['text'])
    print()
    
    # 5. Display results
    print("=" * 60)
    print(f"📋 MEETING: {intelligence.summary.title}")
    print("=" * 60)
    print(f"\n📝 Summary:\n{intelligence.summary.summary}\n")
    
    print(f"🎯 Key Points:")
    for i, point in enumerate(intelligence.summary.key_points, 1):
        print(f"   {i}. {point}")
    
    print(f"\n✅ Action Items ({len(intelligence.action_items)}):")
    for i, item in enumerate(intelligence.action_items, 1):
        owner = f" - {item.owner}" if item.owner else ""
        print(f"   {i}. {item.task}{owner}")
        print(f"      Priority: {item.priority} | {item.context}")
    
    print(f"\n🎯 Decisions ({len(intelligence.decisions)}):")
    for i, decision in enumerate(intelligence.decisions, 1):
        print(f"   {i}. {decision.decision}")
        print(f"      Rationale: {decision.rationale}")
    
    # 6. Save to database
    print(f"\n💾 Saving to database...")
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
    print(f"   ✅ Saved with ID: {meeting.id}")
    
    print("\n" + "=" * 60)
    print("✅ Processing complete!")
    print("=" * 60)
    
    return intelligence


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python simple_processing.py <audio_file>")
        print("Example: python simple_processing.py meeting.mp4")
        sys.exit(1)
    
    file_path = sys.argv[1]
    process_meeting(file_path)
