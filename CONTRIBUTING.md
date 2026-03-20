# Contributing to Meeting Agent

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing.

## Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/meeting-agent.git
   cd meeting-agent
   ```

3. Create a virtual environment:
   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   ```

4. Install with dev dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

5. Set up pre-commit hooks (optional):
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## Development Workflow

1. Create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes

3. Run tests:
   ```bash
   pytest
   ```

4. Format code:
   ```bash
   black .
   ```

5. Lint:
   ```bash
   ruff check .
   ```

6. Commit your changes:
   ```bash
   git add .
   git commit -m "feat: add your feature"
   ```

7. Push and create a pull request

## Commit Message Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

Examples:
```
feat: add Notion integration
fix: resolve diarization memory leak
docs: update installation instructions
```

## Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for public functions
- Keep functions focused and small
- Use meaningful variable names

Example:
```python
def transcribe_audio(audio_path: Path, language: Optional[str] = None) -> Dict:
    """
    Transcribe audio file using Whisper.
    
    Args:
        audio_path: Path to audio file
        language: Language code (e.g., 'en', 'es'). Auto-detect if None.
        
    Returns:
        Dictionary with transcript and metadata
        
    Raises:
        FileNotFoundError: If audio file doesn't exist
    """
    # Implementation
```

## Testing

- Write tests for new features
- Ensure existing tests pass
- Aim for >80% code coverage

Run tests:
```bash
# All tests
pytest

# Specific test file
pytest tests/test_basic.py

# With coverage
pytest --cov=. --cov-report=html
```

## Documentation

- Update README.md for user-facing changes
- Update SETUP.md for installation changes
- Add docstrings to new functions/classes
- Update type hints

## Pull Request Process

1. Update documentation
2. Add tests for new features
3. Ensure all tests pass
4. Update CHANGELOG.md (if exists)
5. Create pull request with clear description
6. Link related issues

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How was this tested?

## Checklist
- [ ] Tests pass
- [ ] Code formatted with black
- [ ] Documentation updated
- [ ] Type hints added
```

## Areas for Contribution

### High Priority
- React approval dashboard UI
- Real-time streaming transcription
- Calendar integration (Google/Outlook)
- Performance optimizations
- Better error handling

### Medium Priority
- Additional LLM providers
- More output formats
- Custom vocabulary support
- Meeting templates
- Analytics dashboard

### Good First Issues
- Documentation improvements
- Example scripts
- Bug fixes
- Test coverage
- Code cleanup

## Architecture Overview

```
meeting-agent/
├── capture/          # Audio/video input
│   ├── file_loader.py
│   ├── mic_recorder.py
│   ├── screen_recorder.py
│   └── system_audio.py
│
├── processing/       # Audio processing & STT
│   ├── preprocessor.py
│   ├── transcriber.py
│   ├── diarizer.py
│   └── vad.py
│
├── intelligence/     # LLM-based extraction
│   ├── chains/
│   │   ├── summarize.py
│   │   ├── action_items.py
│   │   └── decisions.py
│   ├── schemas.py
│   └── pipeline.py
│
├── storage/          # Data persistence
│   ├── database.py
│   ├── notion_writer.py
│   └── obsidian_writer.py
│
├── delivery/         # Output & notifications
│   ├── email_sender.py
│   ├── approver.py
│   └── templates/
│
├── api/              # REST API
│   ├── main.py
│   ├── routes/
│   └── tasks.py
│
└── cli/              # Command-line interface
    └── main.py
```

## Adding New Features

### Adding a New STT Model

1. Update `processing/transcriber.py`
2. Add model configuration to `config.yaml`
3. Update documentation
4. Add tests

### Adding a New LLM Provider

1. Update `intelligence/pipeline.py`
2. Add provider configuration
3. Update environment variables
4. Document API key setup

### Adding a New Integration

1. Create new file in `storage/` or `delivery/`
2. Add configuration to `config.yaml`
3. Update CLI commands if needed
4. Add tests and documentation

## Questions?

- Open an issue for bugs
- Start a discussion for questions
- Check existing issues/PRs first

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help others learn and grow

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
