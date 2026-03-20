#!/bin/bash
# Quick start script for Meeting Agent

set -e

echo "🚀 Meeting Agent Quick Start"
echo "=============================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python $python_version"

# Check ffmpeg
echo "Checking ffmpeg..."
if command -v ffmpeg &> /dev/null; then
    echo "✅ ffmpeg installed"
else
    echo "❌ ffmpeg not found. Please install it:"
    echo "   macOS: brew install ffmpeg"
    echo "   Ubuntu: sudo apt install ffmpeg"
    exit 1
fi

# Check Redis
echo "Checking Redis..."
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo "✅ Redis running"
    else
        echo "⚠️  Redis installed but not running"
        echo "   Start it with: brew services start redis (macOS)"
        echo "   Or: sudo systemctl start redis (Linux)"
    fi
else
    echo "⚠️  Redis not found (optional for API)"
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source .venv/bin/activate

# Install package
echo ""
echo "Installing Meeting Agent..."
pip install -q -e .
echo "✅ Installation complete"

# Check for .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  No .env file found"
    echo "Copying .env.example to .env..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your API keys:"
    echo "   - ANTHROPIC_API_KEY or OPENAI_API_KEY"
    echo "   - HF_TOKEN (from https://huggingface.co/settings/tokens)"
    echo ""
    read -p "Press Enter to continue after editing .env..."
fi

# Run basic test
echo ""
echo "Running basic tests..."
python -c "from capture.file_loader import FileLoader; print('✅ Imports working')"

echo ""
echo "=============================="
echo "✅ Setup complete!"
echo ""
echo "Try these commands:"
echo "  meeting-agent --help"
echo "  meeting-agent process <your_file.mp4>"
echo "  meeting-agent record-mic --duration 10"
echo "  meeting-agent serve"
echo ""
echo "For full documentation, see README.md and SETUP.md"
