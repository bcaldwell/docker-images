#!/usr/bin/env python3
"""
Convert Manning notebook JSON exports to Readwise using their API.
"""

import json
import argparse
import requests
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


def parse_manning_json(json_file: Path) -> Dict[str, Any]:
    """Parse the Manning JSON file and return the parsed data."""
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_highlights_and_notes(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract highlights and notes from Manning data in Readwise API format."""
    items = []
    
    # Get book metadata
    book_title = data.get('product', {}).get('title', 'Unknown Book')
    book_author = data.get('product', {}).get('authors', 'Unknown Author')
    book_cover_url = data.get('product', {}).get('coverPath', '')
    
    # Process each scrapbook item
    for item in data.get('scrapbookItems', []):
        date_created = item.get('dateCreated', '')
        link = item.get('link', '')
        
        # Convert date format from ISO to Readwise API format
        try:
            dt = datetime.fromisoformat(date_created.replace('Z', '+00:00'))
            readwise_date = dt.isoformat()
        except (ValueError, AttributeError):
            readwise_date = None
        
        # Process highlights
        highlights = []
        for highlight in item.get('highlights', []):
            highlight_text = highlight.get('text', '').strip()
            if highlight_text:
                highlights.append(highlight_text)
        
        # Process notes
        notes = []
        for note in item.get('notes', []):
            note_text = note.get('text', '').strip()
            if note_text:
                notes.append(note_text)
        
        # If we have highlights, create entries
        if highlights:
            # Remove duplicate highlights while preserving order
            unique_highlights = []
            for highlight in highlights:
                if highlight not in unique_highlights:
                    unique_highlights.append(highlight)
            
            # Combine all unique highlights with newlines
            combined_highlights = '\n\n'.join(unique_highlights)
            
            # Build the item payload
            item_payload = {
                'text': combined_highlights,
                'title': book_title,
                'author': book_author,
                'source_type': 'manning',
                'category': 'books',
                'location': None,  # No specific location since we're combining items
                'location_type': 'order',
                'highlighted_at': readwise_date,
                'highlight_url': link,  # Specific chapter/section URL
                'image_url': book_cover_url  # Book cover image URL
            }
            
            # Add notes if they exist
            if notes:
                # Remove duplicate notes while preserving order
                unique_notes = []
                for note in notes:
                    if note not in unique_notes:
                        unique_notes.append(note)
                item_payload['note'] = '\n\n'.join(unique_notes)
            
            items.append(item_payload)
    
    return items


def send_to_readwise_api(items: List[Dict[str, Any]], access_token: str, batch_size: int = 100) -> bool:
    """Send highlights to Readwise API in batches."""
    api_url = "https://readwise.io/api/v2/highlights/"
    headers = {
        "Authorization": f"Token {access_token}",
        "Content-Type": "application/json"
    }
    
    # Process items in batches to avoid overwhelming the API
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        
        payload = {"highlights": batch}
        
        try:
            print(f"Sending batch {i//batch_size + 1} ({len(batch)} items)...")
            response = requests.post(api_url, headers=headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Successfully sent batch. Created/updated {len(result)} books.")
                
                # Show details about created books
                for book in result:
                    print(f"   📚 {book['title']} by {book['author']} ({book['num_highlights']} highlights)")
                    
            elif response.status_code == 429:
                retry_after = response.headers.get('Retry-After', 60)
                print(f"⚠️  Rate limited. Waiting {retry_after} seconds...")
                import time
                time.sleep(int(retry_after))
                # Retry this batch
                i -= batch_size
                continue
                
            else:
                print(f"❌ Error sending batch: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error: {e}")
            return False
    
    return True


def main():
    """Main function to handle command line arguments and conversion."""
    parser = argparse.ArgumentParser(
        description='Convert Manning notebook JSON to Readwise using their API'
    )
    parser.add_argument(
        '--input', '-i',
        required=True,
        type=Path,
        help='Input Manning JSON file path'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Number of highlights to send per API request (default: 100)'
    )
    
    args = parser.parse_args()
                
    # Get token from environment variable
    token = os.environ.get('READWISE_TOKEN')
    if not token:
        print("Error: READWISE_TOKEN environment variable is required.")
        print("Set it with: export READWISE_TOKEN=your_token_here")
        print("Get your token from: https://readwise.io/access_token")
        return 1
    
    # Validate input file exists
    if not args.input.exists():
        print(f"Error: Input file '{args.input}' does not exist.")
        return 1

    try:
        # Parse Manning JSON
        print(f"Parsing Manning JSON file: {args.input}")
        data = parse_manning_json(args.input)
        
        # Extract highlights and notes
        print("Extracting highlights and notes...")
        items = extract_highlights_and_notes(data)
        
        print(f"Found {len(items)} highlights and notes to send to Readwise")
        
        # Send to Readwise API
        print("Sending to Readwise API...")
        success = send_to_readwise_api(items, token, args.batch_size)
        
        if success:
            print(f"✅ Successfully sent all {len(items)} items to Readwise!")
            print("All highlights are now grouped under one book in your Readwise account.")
        else:
            print("❌ Failed to send some items to Readwise.")
            return 1
            
        return 0
        
    except Exception as e:
        print(f"Error during conversion: {e}")
        return 1


if __name__ == '__main__':
    exit(main())