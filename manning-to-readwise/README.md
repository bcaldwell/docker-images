# Manning to Readwise Converter

A Python tool to convert Manning notebook JSON exports to Readwise using their API.

## Features

- Parse Manning notebook JSON exports
- Send highlights directly to Readwise via their API
- Preserve highlights, notes, and metadata
- **Properly groups all highlights under one book** (solves the CSV import issue)
- Support for batch processing with rate limiting
- Real-time feedback on API responses
- Option to merge sequential highlights with the same ID into consolidated items

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd manning-to-readwise

# Install with uv
uv sync
```

## Setup

1. **Get your Readwise API token** from [readwise.io/access_token](https://readwise.io/access_token)
2. **Install dependencies**: `uv sync`
3. **Set your API token**:
   ```bash
   export READWISE_TOKEN=your_token_here
   ```

## Usage

### Command Line Interface

```bash
# Set your API token
export READWISE_TOKEN=your_token_here

# Run the converter
python src/manning_to_readwise.py --input notebook.json
```

Or with short options:
```bash
python src/manning_to_readwise.py -i notebook.json
```

### Batch Size Control

```bash
# Send highlights in smaller batches (useful for large notebooks)
python src/manning_to_readwise.py -i notebook.json --batch-size 50

# Merge sequential highlights with the same ID into one item
python src/manning_to_readwise.py -i notebook.json --merge-sequential
```

## How It Works

1. **Parses** the Manning JSON export file
2. **Extracts** all highlights and notes from the scrapbook items
3. **Groups** all highlights under the main book URL (not individual chapter URLs)
4. **Sends** highlights to Readwise API in configurable batches
5. **Handles** rate limiting automatically
6. **Provides** real-time feedback on the import process

## Why API Instead of CSV?

- ✅ **Proper book grouping**: All highlights appear under one book instead of being split by chapter URLs
- ✅ **Real-time feedback**: See exactly what's being imported and any errors
- ✅ **Rate limiting**: Automatically handles API limits
- ✅ **No manual import**: Highlights appear in Readwise immediately
- ✅ **Better metadata**: Preserves location offsets and timestamps properly

## API Response Example

```
✅ Successfully sent batch. Created/updated 1 books.
   📚 Unit Testing Principles, Practices, and Patterns by Vladimir Khorikov (153 highlights)
```

## Development

The project is structured to be easily extensible:

- `src/manning_to_readwise.py` - Main conversion logic and API integration
- `pyproject.toml` - Project configuration with uv

## License

MIT 