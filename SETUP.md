# Setup Guide

Complete setup instructions for Meeting Agent.

## Step 1: System Dependencies

### macOS

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.12 ffmpeg redis

# Start Redis
brew services start redis
```

### Ubuntu/Debian

```bash
# Update package list
sudo apt update

# Install dependencies
sudo apt install -y python3.12 python3.12-venv python3-pip ffmpeg redis-server portaudio19-dev

# Start Redis
sudo systemctl start redis
sudo systemctl enable redis
```

### Windows

1. Install Python 3.12 from https://www.python.org/downloads/
2. Install ffmpeg:
   - Download from https://ffmpeg.org/download.html
   - Extract and add to PATH
3. Install Redis:
   - Download from https://github.com/microsoftarchive/redis/releases
   - Or use WSL2 with Ubuntu

## Step 2: Python Environment

```bash
# Clone the repository
git clone <repository-url>
cd meeting-agent

# Create virtual environment
python3.12 -m venv .venv

# Activate virtual environment
# macOS/Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# Install the package
pip install -e .

# Or with development dependencies
pip install -e ".[dev]"
```

## Step 3: Configuration

### 1. Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your favorite editor
nano .env  # or vim, code, etc.
```

Required variables:
```env
# Choose one LLM provider
ANTHROPIC_API_KEY=sk-ant-...        # Get from https://console.anthropic.com/
# OR
OPENAI_API_KEY=sk-...               # Get from https://platform.openai.com/

# Required for speaker diarization
HF_TOKEN=hf_...                     # Get from https://huggingface.co/settings/tokens

# Optional: Email integration
EMAIL_USERNAME=your_email@gmail.com
EMAIL_APP_PASSWORD=your_app_password  # Gmail: https://myaccount.google.com/apppasswords
EMAIL_FROM=your_email@gmail.com

# Optional: Notion integration
NOTION_TOKEN=secret_...
NOTION_DATABASE_ID=...
```

### 2. HuggingFace Token Setup

1. Go to https://huggingface.co/settings/tokens
2. Create a new token with "Read" access
3. Accept the pyannote model terms:
   - Visit https://huggingface.co/pyannote/speaker-diarization-3.1
   - Click "Agree and access repository"
4. Add token to `.env`

### 3. Gmail App Password (for email integration)

1. Enable 2-factor authentication on your Google account
2. Go to https://myaccount.google.com/apppasswords
3. Generate an app password for "Mail"
4. Add to `.env` as `EMAIL_APP_PASSWORD`

### 4. Anthropic API Key (recommended)

1. Sign up at https://console.anthropic.com/
2. Create an API key
3. Add to `.env` as `ANTHROPIC_API_KEY`

Cost: ~$0.05-0.10 per hour-long meeting with Claude Haiku

### 5. Customize config.yaml (optional)

```yaml
# Choose STT model based on your hardware
stt:
  model: "distil-large-v3"  # Good balance
  # model: "tiny"           # Fast, lower accuracy
  # model: "large-v3-turbo" # Best accuracy, needs GPU

# Choose LLM provider
llm:
  provider: "anthropic"     # Recommended
  model: "claude-3-5-haiku-20241022"
  # provider: "openai"
  # model: "gpt-4o-mini"
  # provider: "ollama"      # Local, free
  # model: "llama3"
```

## Step 4: Verify Installation

```bash
# Test imports
python -c "from capture.file_loader import FileLoader; print('✅ Imports working')"

# Run tests
pytest tests/

# Check CLI
meeting-agent --help
```

## Step 5: First Run

### Process a test file

```bash
# Download a sample audio file or use your own
meeting-agent process your_meeting.mp4

# Or skip diarization for faster testing
meeting-agent process your_meeting.mp4 --skip-diarization
```

### Record a test

```bash
# Record 10 seconds from microphone
meeting-agent record-mic --duration 10

# Process the recording
meeting-agent process recording_mic_*.wav
```

## Step 6: Start Services (for API)

### Terminal 1: Redis (if not running as service)

```bash
redis-server
```

### Terminal 2: Celery Worker

```bash
celery -A api.tasks worker --loglevel=info
```

### Terminal 3: API Server

```bash
meeting-agent serve
```

Visit http://localhost:8000/docs for API documentation.

## Step 7: Docker Setup (Alternative)

```bash
# Copy environment file
cp .env.example .env

# Edit .env with your API keys
nano .env

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Troubleshooting

### "No module named 'faster_whisper'"

```bash
pip install faster-whisper
```

### "Could not load model"

First run downloads models (~750MB for distil-large-v3). Ensure you have:
- Internet connection
- ~2GB free disk space
- Patience (5-10 minutes)

### "HuggingFace token required"

1. Get token from https://huggingface.co/settings/tokens
2. Accept pyannote terms at https://huggingface.co/pyannote/speaker-diarization-3.1
3. Set `HF_TOKEN` in `.env`

### "ffmpeg not found"

Install ffmpeg (see Step 1)

### "Redis connection refused"

```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# If not, start Redis
# macOS:
brew services start redis
# Linux:
sudo systemctl start redis
```

### Slow transcription

Try a smaller model in `config.yaml`:
```yaml
stt:
  model: "base"  # or "tiny"
```

### Out of memory

Reduce model size or use int8 quantization:
```yaml
stt:
  model: "base"
  compute_type: "int8"
```

## Next Steps

1. Read the [README.md](README.md) for usage examples
2. Check the [architecture diagram](meeting_agent_full_pipeline.html)
3. Explore the API at http://localhost:8000/docs
4. Customize `config.yaml` for your needs
5. Set up integrations (Notion, Obsidian, email)

## Getting Help

- Check existing issues on GitHub
- Read the documentation
- Ask in discussions

## Development Setup

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .

# Lint
ruff check .

# Type check
mypy .
```
