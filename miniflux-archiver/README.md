# Miniflux Archiver

A Python tool to automatically archive outdated feed items in Miniflux based on configurable rules.

## Features
- Automatically archive old feed items based on configurable rules
- Integration with Miniflux API
- Rule-based archiving system

## Requirements
- Python 3.8+
- uv (Python package manager)
- Miniflux instance and API key

## Setup
1. Install uv if not already installed:
```bash
pip install uv
```

2. Create a new virtual environment and install dependencies:
```bash
uv venv
source .venv/bin/activate  # On Unix-like systems
# OR
.venv\Scripts\activate     # On Windows

uv pip install .
```

3. Copy the example configuration:
```bash
cp config.example.yaml config.yaml
```

4. Update the configuration with your Miniflux details

## Usage
```bash
python main.py
```

## Configuration
Edit `config.yaml` to set up your rules for archiving. Example configuration:

```yaml
miniflux:
  url: "https://your-miniflux-instance"
  api_key: "your-api-key"

rules:
  - age_days: 30  # Archive items older than 30 days
    categories: ["news", "tech"]  # Apply to these categories
  - age_days: 90  # Archive items older than 90 days
    feeds: ["feed-id-1", "feed-id-2"]  # Apply to specific feeds
``` 