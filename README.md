# Meeting Agent 🎙️

AI-powered meeting transcription and intelligence extraction system. Automatically transcribe meetings, identify speakers, extract action items, capture decisions, and send follow-up emails.

## Features

- **Multi-source capture**: Record from microphone, screen, system audio, or upload files
- **High-quality transcription**: Uses faster-whisper with distil-large-v3 for accurate, CPU-friendly transcription
- **Speaker diarization**: Identifies who said what using pyannote-audio
- **Intelligence extraction**: Automatically extracts summaries, action items, and decisions using LLMs
- **Multiple outputs**: Save to SQLite, Notion, Obsidian, or send via email
- **Background processing**: Async task queue with Celery for long-running jobs
- **REST API**: FastAPI server with upload and status endpoints
- **CLI interface**: Rich terminal interface for all operations

## Architecture

```
Audio Input → Preprocessing → STT → Diarization → Intelligence → Storage/Delivery
```

See `meeting_agent_full_pipeline.html` for detailed architecture visualization.

## Installation

### Prerequisites

- Python 3.12+
- ffmpeg (for audio processing)
- Redis (for background tasks)

### Install ffmpeg

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

### Install Redis

```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis

# Windows
# Download from https://redis.io/download
```

### Install Meeting Agent

```bash
# Clone repository
git clone <repository-url>
cd meeting-agent

# Install with uv (recommended)
uv pip install -e .

# Or with pip
pip install -e .
```

## Configuration

1. Copy the example environment file:

```bash
cp .env.example .env
```

2. Edit `.env` and add your API keys:

```env
ANTHROPIC_API_KEY=your_key_here
HF_TOKEN=your_huggingface_token_here
EMAIL_USERNAME=your_email@gmail.com
EMAIL_APP_PASSWORD=your_app_password
```

3. (Optional) Customize `config.yaml` for model selection, LLM provider, etc.

## Quick Start

### Process an existing recording

```bash
meeting-agent process recording.mp4
```

### Record from microphone

```bash
meeting-agent record-mic --duration 60
# Or press Ctrl+C to stop
```

### Record screen with audio

```bash
meeting-agent record-screen
# Press Ctrl+C to stop
```

### List meetings

```bash
meeting-agent list-meetings
```

### Start API server

```bash
meeting-agent serve
```

Then visit http://localhost:8000/docs for API documentation.


## Widget (Desktop Overlay)

Run the floating widget:

```bash
uv run meeting-widget
```

### Widget recording modes

- **Screen**: records desktop + default audio device through ffmpeg.
- **Mic**: records microphone through PortAudio (`sounddevice`).
- **System**: records loopback/system output (`soundcard`) if your OS/driver supports it.

If a mode is unavailable, the widget now surfaces a clear runtime error instead of hanging.

### Where files are stored

Recordings are written to the current working directory where you launch `meeting-widget`.
The widget status line shows both filename and parent directory after stop.

## Build / distribute to users

Use PyInstaller to ship a single executable.

```bash
# install tooling
uv pip install pyinstaller

# build widget executable
pyinstaller --onefile --name meeting-widget widget/app.py
```

Output binary location:
- macOS/Linux: `dist/meeting-widget`
- Windows: `dist/meeting-widget.exe`

### Runtime dependencies by platform

- **All platforms**: `ffmpeg` must be installed and on PATH for screen capture.
- **Windows**: audio devices + PortAudio backend required.
- **macOS**: grant Microphone + Screen Recording permissions in System Settings.
- **Linux**: PulseAudio/PipeWire recommended; system loopback may need monitor/virtual sink.

## Usage Examples

### CLI Processing

```bash
# Process with all features
meeting-agent process meeting.mp4

# Skip speaker diarization (faster)
meeting-agent process meeting.mp4 --skip-diarization

# Save output to JSON
meeting-agent process meeting.mp4 --output result.json
```

### API Usage

```python
import requests

# Upload file
with open('meeting.mp4', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/upload/',
        files={'file': f}
    )
job_id = response.json()['job_id']

# Check status
status = requests.get(f'http://localhost:8000/api/jobs/{job_id}')
print(status.json())

# Get meeting details
meetings = requests.get('http://localhost:8000/api/meetings/')
print(meetings.json())
```

### Python API

```python
from pathlib import Path
from processing.transcriber import Transcriber
from intelligence.pipeline import IntelligencePipeline

# Transcribe
transcriber = Transcriber()
transcript = transcriber.transcribe(Path("meeting.wav"))

# Extract intelligence
pipeline = IntelligencePipeline()
intelligence = pipeline.process_sync(transcript['text'])

print(f"Title: {intelligence.summary.title}")
print(f"Action items: {len(intelligence.action_items)}")
```

## Model Selection

The system auto-detects your hardware and selects the best model. You can override in `config.yaml`:

### CPU-only (default)
```yaml
stt:
  model: "distil-large-v3"  # Fast, accurate, CPU-friendly
  device: "cpu"
  compute_type: "int8"
```

### GPU
```yaml
stt:
  model: "large-v3-turbo"
  device: "cuda"
  compute_type: "float16"
```

### Low-end hardware
```yaml
stt:
  model: "tiny"  # or "base"
  device: "cpu"
  compute_type: "int8"
```

## LLM Providers

### Anthropic (default)
```yaml
llm:
  provider: "anthropic"
  model: "claude-3-5-haiku-20241022"
```

### OpenAI
```yaml
llm:
  provider: "openai"
  model: "gpt-4o-mini"
```

### Local (Ollama)
```yaml
llm:
  provider: "ollama"
  model: "llama3"
```

## Integrations

### Email Follow-ups

Configure in `config.yaml`:

```yaml
integrations:
  email:
    enabled: true
    smtp_host: "smtp.gmail.com"
    smtp_port: 587
```

Set environment variables:
```bash
EMAIL_USERNAME=your_email@gmail.com
EMAIL_APP_PASSWORD=your_app_password
EMAIL_FROM=your_email@gmail.com
```

### Notion

1. Create a Notion integration at https://www.notion.so/my-integrations
2. Share a database with your integration
3. Configure:

```yaml
integrations:
  notion:
    enabled: true
```

```bash
NOTION_TOKEN=your_token
NOTION_DATABASE_ID=your_database_id
```

### Obsidian

```yaml
integrations:
  obsidian:
    enabled: true
    vault_path: "~/Documents/Obsidian/Meetings"
```

## Background Processing

Start Celery worker for async processing:

```bash
celery -A api.tasks worker --loglevel=info
```

## Development

### Project Structure

```
meeting-agent/
├── capture/          # Audio/video capture
├── processing/       # STT and preprocessing
├── intelligence/     # LLM chains for extraction
├── storage/          # Database and integrations
├── delivery/         # Email and notifications
├── api/              # FastAPI server
├── cli/              # CLI interface
└── config.yaml       # Configuration
```

### Running Tests

```bash
pytest
```

### Code Quality

```bash
# Format
black .

# Lint
ruff check .

# Type check
mypy .
```

## Docker Deployment

```bash
docker-compose up -d
```

This starts:
- Meeting Agent API
- Redis
- Celery worker

## Performance

- **Transcription**: ~0.2x realtime on CPU (1 hour meeting = 12 minutes)
- **Diarization**: ~0.5x realtime on CPU
- **Intelligence**: ~30 seconds for 1 hour meeting
- **Total**: ~15-20 minutes for 1 hour meeting on mid-range CPU

## Costs

Using Claude Haiku or GPT-4o-mini:
- ~$0.05-0.10 per hour-long meeting
- Transcription is free (local)
- Diarization is free (local)

## Troubleshooting

### "No module named 'faster_whisper'"

```bash
pip install faster-whisper
```

### "HuggingFace token required"

Get token from https://huggingface.co/settings/tokens and set:
```bash
export HF_TOKEN=your_token
```

### "ffmpeg not found"

Install ffmpeg (see Installation section)

### Slow transcription

Try a smaller model:
```yaml
stt:
  model: "base"  # or "tiny"
```

## Roadmap

- [ ] React approval dashboard UI
- [ ] Real-time streaming transcription
- [ ] Multi-language support
- [ ] Calendar integration (Google/Outlook)
- [ ] Slack/Teams notifications
- [ ] Custom vocabulary/terminology
- [ ] Meeting templates
- [ ] Analytics dashboard

## Contributing

Contributions welcome! Please read CONTRIBUTING.md first.

## License

MIT License - see LICENSE file

## Credits

Built with:
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) - STT
- [pyannote-audio](https://github.com/pyannote/pyannote-audio) - Diarization
- [LangChain](https://github.com/langchain-ai/langchain) - LLM orchestration
- [FastAPI](https://fastapi.tiangolo.com/) - API framework
- [Typer](https://typer.tiangolo.com/) - CLI framework
