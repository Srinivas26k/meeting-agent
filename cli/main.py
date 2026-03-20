"""CLI application using Typer."""
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path
from typing import Optional
import time

# Import our modules
from capture.file_loader import FileLoader
from capture.mic_recorder import MicRecorder
from capture.screen_recorder import ScreenRecorder
from capture.system_audio import SystemAudioRecorder
from processing.preprocessor import AudioPreprocessor
from processing.transcriber import Transcriber
from processing.diarizer import Diarizer
from intelligence.pipeline import IntelligencePipeline
from storage.database import Database
from delivery.email_sender import create_email_sender_from_config
import yaml

app = typer.Typer(help="Meeting Agent - AI-powered meeting transcription and intelligence")
console = Console()


@app.command()
def process(
    file_path: str = typer.Argument(..., help="Path to audio/video file"),
    skip_diarization: bool = typer.Option(False, "--skip-diarization", help="Skip speaker diarization"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output JSON file path"),
):
    """Process a meeting recording file."""
    console.print(f"\n[bold blue]🎯 Processing meeting recording...[/bold blue]\n")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # Load file
            task = progress.add_task("Loading file...", total=None)
            file_path_obj = FileLoader.load(file_path)
            info = FileLoader.get_file_info(file_path_obj)
            console.print(f"✅ Loaded: {info['name']} ({info['size_mb']:.1f} MB)")
            progress.remove_task(task)
            
            # Preprocess audio
            task = progress.add_task("Preprocessing audio...", total=None)
            preprocessor = AudioPreprocessor()
            processed_audio = preprocessor.process(file_path_obj)
            progress.remove_task(task)
            
            # Transcribe
            task = progress.add_task("Transcribing (this may take a while)...", total=None)
            transcriber = Transcriber()
            transcript = transcriber.transcribe(processed_audio)
            progress.remove_task(task)
            
            # Diarization
            if not skip_diarization:
                task = progress.add_task("Diarizing speakers...", total=None)
                try:
                    diarizer = Diarizer()
                    diarization = diarizer.diarize(processed_audio)
                    merged_transcript = diarizer.merge_with_transcript(transcript, diarization)
                    
                    # Format transcript with speakers
                    formatted_text = "\n\n".join([
                        f"{seg['speaker']}: {seg['text']}"
                        for seg in merged_transcript
                    ])
                except Exception as e:
                    console.print(f"[yellow]⚠️  Diarization failed: {e}[/yellow]")
                    formatted_text = transcript['text']
                progress.remove_task(task)
            else:
                formatted_text = transcript['text']
            
            # Intelligence extraction
            task = progress.add_task("Extracting intelligence...", total=None)
            pipeline = IntelligencePipeline()
            intelligence = pipeline.process_sync(formatted_text)
            progress.remove_task(task)
            
            # Save to database
            task = progress.add_task("Saving to database...", total=None)
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
            progress.remove_task(task)
        
        # Display results
        console.print(f"\n[bold green]✅ Processing complete![/bold green]\n")
        console.print(f"[bold]Meeting:[/bold] {intelligence.summary.title}")
        console.print(f"[bold]Summary:[/bold] {intelligence.summary.summary[:200]}...")
        console.print(f"\n[bold]Action Items:[/bold] {len(intelligence.action_items)}")
        for item in intelligence.action_items[:3]:
            console.print(f"  • {item.task} ({item.owner or 'Unassigned'})")
        
        console.print(f"\n[bold]Decisions:[/bold] {len(intelligence.decisions)}")
        for dec in intelligence.decisions[:3]:
            console.print(f"  • {dec.decision}")
        
        console.print(f"\n💾 Saved to database (ID: {meeting.id})")
        
        # Save to JSON if requested
        if output:
            import json
            output_path = Path(output)
            output_path.write_text(json.dumps(intelligence.dict(), indent=2, default=str))
            console.print(f"📄 Saved to: {output}")
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Error: {e}[/bold red]")
        raise typer.Exit(1)


@app.command()
def record_mic(
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
    duration: Optional[int] = typer.Option(None, "--duration", "-d", help="Recording duration in seconds"),
):
    """Record audio from microphone."""
    console.print("\n[bold blue]🎤 Starting microphone recording...[/bold blue]")
    console.print("Press Ctrl+C to stop recording\n")
    
    recorder = MicRecorder()
    recorder.start()
    
    try:
        if duration:
            time.sleep(duration)
        else:
            # Wait for Ctrl+C
            while True:
                time.sleep(0.1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping recording...[/yellow]")
    
    output_path = recorder.stop(output)
    console.print(f"\n[bold green]✅ Recording saved: {output_path}[/bold green]")
    console.print(f"\nProcess it with: [bold]meeting-agent process {output_path}[/bold]")


@app.command()
def record_screen(
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Record screen with audio."""
    console.print("\n[bold blue]🎬 Starting screen recording...[/bold blue]")
    console.print("Press Ctrl+C to stop recording\n")
    
    recorder = ScreenRecorder()
    output_path = recorder.start(output)
    
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping recording...[/yellow]")
    
    output_path = recorder.stop()
    console.print(f"\n[bold green]✅ Recording saved: {output_path}[/bold green]")
    console.print(f"\nProcess it with: [bold]meeting-agent process {output_path}[/bold]")


@app.command()
def list_meetings(
    limit: int = typer.Option(10, "--limit", "-n", help="Number of meetings to show"),
):
    """List recent meetings."""
    db = Database()
    meetings = db.list_meetings(limit=limit)
    
    if not meetings:
        console.print("[yellow]No meetings found[/yellow]")
        return
    
    console.print(f"\n[bold]Recent Meetings:[/bold]\n")
    for meeting in meetings:
        console.print(f"[bold]ID {meeting.id}:[/bold] {meeting.title}")
        console.print(f"  Date: {meeting.date.strftime('%Y-%m-%d %H:%M')}")
        console.print(f"  Participants: {meeting.participants}")
        console.print()


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind to"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload"),
):
    """Start the FastAPI server."""
    import uvicorn
    
    console.print(f"\n[bold blue]🚀 Starting API server...[/bold blue]")
    console.print(f"Server will be available at: http://{host}:{port}\n")
    
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=reload
    )


if __name__ == "__main__":
    app()
