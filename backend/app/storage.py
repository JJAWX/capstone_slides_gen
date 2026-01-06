import json
import os
import logging
from pathlib import Path
from typing import Dict, Any
import threading

logger = logging.getLogger(__name__)


class DeckStorage:
    """
    Persistent storage for deck data using JSON file.
    Provides thread-safe operations for saving and loading deck metadata.
    """

    def __init__(self, storage_file: str = "backend/data/decks.json"):
        self.storage_file = storage_file
        self.lock = threading.Lock()
        self._ensure_storage_dir()

    def _ensure_storage_dir(self):
        """Ensure the storage directory exists."""
        storage_dir = os.path.dirname(self.storage_file)
        if storage_dir:
            os.makedirs(storage_dir, exist_ok=True)
            logger.info(f"Storage directory ensured: {storage_dir}")

    def load(self) -> Dict[str, Any]:
        """
        Load deck data from JSON file.

        Returns:
            Dict containing all deck data
        """
        with self.lock:
            if not os.path.exists(self.storage_file):
                logger.info("Storage file not found, starting with empty storage")
                return {}

            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Loaded {len(data)} decks from storage")
                    return data
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON from storage file: {e}")
                return {}
            except Exception as e:
                logger.error(f"Error loading storage: {e}")
                return {}

    def save(self, data: Dict[str, Any]):
        """
        Save deck data to JSON file.

        Args:
            data: Dict containing all deck data
        """
        with self.lock:
            try:
                # Create backup of existing file
                if os.path.exists(self.storage_file):
                    backup_file = f"{self.storage_file}.backup"
                    try:
                        with open(self.storage_file, 'r') as f:
                            backup_data = f.read()
                        with open(backup_file, 'w') as f:
                            f.write(backup_data)
                    except Exception as e:
                        logger.warning(f"Failed to create backup: {e}")

                # Save new data
                with open(self.storage_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                logger.debug(f"Saved {len(data)} decks to storage")

            except Exception as e:
                logger.error(f"Error saving storage: {e}")
                raise

    def update_deck(self, deck_id: str, deck_data: Dict[str, Any], all_data: Dict[str, Any]):
        """
        Update a single deck and save to storage.

        Args:
            deck_id: The deck ID to update
            deck_data: The new deck data
            all_data: Reference to the complete decks_storage dict
        """
        all_data[deck_id] = deck_data
        self.save(all_data)

    def delete_deck(self, deck_id: str, all_data: Dict[str, Any]):
        """
        Delete a deck and save to storage.

        Args:
            deck_id: The deck ID to delete
            all_data: Reference to the complete decks_storage dict
        """
        if deck_id in all_data:
            del all_data[deck_id]
            self.save(all_data)
            logger.info(f"Deleted deck {deck_id} from storage")

    def clear(self):
        """Clear all data from storage."""
        with self.lock:
            try:
                if os.path.exists(self.storage_file):
                    os.remove(self.storage_file)
                logger.info("Storage cleared")
            except Exception as e:
                logger.error(f"Error clearing storage: {e}")
                raise


# Global storage instance
deck_storage = DeckStorage()
