"""Main entry point for Meeting Agent."""
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def main():
    """Main entry point."""
    print("Meeting Agent - AI-powered meeting transcription and intelligence")
    print("\nUse the CLI commands:")
    print("  meeting-agent process <file>     - Process a recording file")
    print("  meeting-agent record-mic         - Record from microphone")
    print("  meeting-agent record-screen      - Record screen with audio")
    print("  meeting-agent list-meetings      - List recent meetings")
    print("  meeting-agent serve              - Start API server")
    print("\nFor help: meeting-agent --help")


if __name__ == "__main__":
    main()
