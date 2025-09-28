#!/usr/bin/env python3

import os
import logging
import yaml
from pathlib import Path
from datetime import datetime, timedelta
from dateutil.parser import parse as parse_date
from miniflux import Client
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class LoggingConfig:
    level: str = "INFO"

@dataclass
class MinifluxConfig:
    url: str

@dataclass
class ArchiveRule:
    age_days: Optional[int] = None
    reading_time_min: Optional[int] = None
    categories: Optional[List[str]] = None
    feeds: Optional[List[int]] = None
    exclude_feeds: Optional[List[int]] = None

    def __post_init__(self):
        if self.age_days is None and self.reading_time_min is None:
            raise ValueError("Each rule must have either 'age_days' or 'reading_time_min'")

@dataclass
class Config:
    miniflux: MinifluxConfig
    rules: List[ArchiveRule]
    logging: LoggingConfig = field(default_factory=LoggingConfig)

def setup_logging(level: str = "INFO") -> None:
    """Configure logging."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

class Archiver:
    def __init__(self, client: Client, rules: List[ArchiveRule], dry_run: bool = False) -> None:
        self.client = client
        self.rules = rules
        self.dry_run = dry_run
        self.logger = logging.getLogger(__name__)
        # Cache feed names for lookup
        self.feed_names = {feed['id']: feed['title'] for feed in self.client.get_feeds()}
    
    def should_archive(self, entry: dict, rule: ArchiveRule) -> bool:
        """Check if an entry should be archived based on a rule."""
        # Check age-based rules
        if rule.age_days is not None:
            entry_date = parse_date(entry['published_at'])
            age_limit = datetime.now(entry_date.tzinfo) - timedelta(days=rule.age_days)
            if entry_date > age_limit:
                return False

        # Check reading time rules
        if rule.reading_time_min is not None:
            reading_time = entry.get('reading_time', 0)
            if reading_time >= rule.reading_time_min:
                return False
            
        # Check category filters
        if rule.categories:
            if not any(cat.lower() in (entry.get('feed', {}).get('category', '').lower() for cat in rule.categories)):
                return False
                
        # Check feed filters by name
        if rule.feeds:
            feed_name = self.feed_names.get(entry.get('feed_id'), '').lower()
            if not any(feed.lower() in feed_name for feed in rule.feeds):
                return False

        if rule.exclude_feeds:
            feed_name = self.feed_names.get(entry.get('feed_id'), '').lower()
            if any(feed.lower() in feed_name for feed in rule.exclude_feeds):
                return False
                
        return True
    
    def run(self) -> None:
        """Run the archiving process."""
        self.logger.info("Starting archiving process...")
        
        batch_size = 100
        total_archived = 0

        
        # Get initial batch to determine total entries
        initial_batch = self.client.get_entries(status="unread", limit=1, offset=0)
        total_entries = initial_batch['total']
        
        # Process entries in batches
        for offset in range(0, total_entries, batch_size):
            entries = self.client.get_entries(status="unread", limit=batch_size, offset=offset)
            if not entries['entries']:
                break
                
            to_archive = []
            for entry in entries['entries']:
                for rule in self.rules:
                    if not self.should_archive(entry, rule):
                        continue

                    reason = "unknown reason"
                    if rule.age_days is not None:
                        entry_date = parse_date(entry['published_at'])
                        age = (datetime.now(entry_date.tzinfo) - entry_date).days
                        reason = f"age={entry_date.strftime('%Y-%m-%d')} ({age} days old) > {rule.age_days} days"
                    elif rule.reading_time_min is not None:
                        reason = f"reading_time={entry.get('reading_time', 0)}min < {rule.reading_time_min}min"

                    to_archive.append(entry['id'])
                    self.logger.info(f"Will archive: {entry['feed']['title']} - {entry['title']} ({reason})")
                    break
            if to_archive:
                if not self.dry_run:
                    self.client.update_entries(entry_ids=to_archive, status="read")
                    self.logger.info(f"Archived {len(to_archive)} entries")
                else:
                    self.logger.info(f"(DRY RUN) - Would archive {len(to_archive)} entries")
                total_archived += len(to_archive)
            
        self.logger.info(f"Archiving complete. Total entries {'would be ' if self.dry_run else ''}archived: {total_archived}")

    def print_feed_hierarchy(self) -> None:
        """Print all feeds and their categories in a tree structure."""
        feeds = self.client.get_feeds()
        categories = {}
        
        # Group feeds by category
        for feed in feeds:
            category = feed.get('category', {})
            category_title = category.get('title', 'Uncategorized')
            category_id = category.get('id', '')
            if category_title not in categories:
                categories[category_title] = {'id': category_id, 'feeds': []}
            categories[category_title]['feeds'].append(feed)
        
        # Print tree structure
        print("\nFeed Hierarchy:")
        print("==============")
        for category_title, data in sorted(categories.items()):
            category_id = data['id']
            feeds = data['feeds']
            print(f"\n{category_title} (ID: {category_id})")
            for feed in sorted(feeds, key=lambda x: x['title']):
                print(f"  ├─ {feed['title']} (ID: {feed['id']})")

def load_config(config_path: str) -> Config:
    """Load and validate the configuration file."""
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
    with open(config_file) as f:
        try:
            raw_config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in configuration file: {e}")
    
    try:
        # Convert raw dictionaries to dataclasses
        miniflux_config = MinifluxConfig(**raw_config['miniflux'])
        rules = [ArchiveRule(**rule) for rule in raw_config['rules']]
        logging_config = LoggingConfig(**raw_config.get('logging', {}))
        
        return Config(
            miniflux=miniflux_config,
            rules=rules,
            logging=logging_config
        )
    except (KeyError, TypeError) as e:
        raise ValueError(f"Invalid configuration structure: {e}")

def get_api_key() -> str:
    """Get the Miniflux API key from environment variables."""
    api_key = os.environ.get('MINIFLUX_API_KEY')
    if not api_key:
        raise ValueError(
            "Miniflux API key not found. Please set the MINIFLUX_API_KEY environment variable."
        )
    return api_key

def main() -> None:
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Archive old Miniflux entries based on rules.")
    parser.add_argument("--config", "-c", default="config.yaml", help="Path to configuration file")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be archived without making changes")
    parser.add_argument("--list-feeds", action="store_true", help="Print all feeds and their categories")
    args = parser.parse_args()

    try:
        config = load_config(args.config)
        setup_logging(level=config.logging.level)
        
        api_key = get_api_key()
        client = Client(
            base_url=config.miniflux.url,
            api_key=api_key
        )
        
        archiver = Archiver(client, config.rules, dry_run=args.dry_run)
        
        if args.list_feeds:
            archiver.print_feed_hierarchy()
            return
            
        archiver.run()
        
    except Exception as e:
        logging.error(str(e))
        raise

if __name__ == "__main__":
    main() 
