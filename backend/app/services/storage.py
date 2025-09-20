import json
from pathlib import Path
from typing import Dict, Optional, Any
from ..models.poll import Poll

class FileStorage:
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / 'data'
        self.data_dir.mkdir(exist_ok=True)
        self.polls_file = self.data_dir / 'polls.json'
        self._polls: Dict[str, dict] = self._load_polls()

    def _load_polls(self) -> Dict[str, dict]:
        print(f"Loading polls from {self.polls_file}")
        if not self.polls_file.exists():
            print("Polls file does not exist, creating empty storage")
            return {}
        try:
            with open(self.polls_file, 'r') as f:
                polls = json.load(f)
                print(f"Loaded {len(polls)} polls from storage")
                return polls
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading polls: {str(e)}")
            return {}

    def _save_polls(self):
        print(f"Saving {len(self._polls)} polls to {self.polls_file}")
        try:
            with open(self.polls_file, 'w') as f:
                json.dump(self._polls, f, indent=2)
            print("Polls saved successfully")
        except Exception as e:
            print(f"Error saving polls: {str(e)}")
            raise

    def get_poll(self, poll_id: str) -> Optional[Poll]:
        poll_data = self._polls.get(poll_id)
        if poll_data:
            return Poll(**poll_data)
        return None

    def save_poll(self, poll: Poll):
        self._polls[poll.id] = poll.dict()
        self._save_polls()

    def get_all_polls(self) -> list[Poll]:
        return [Poll(**poll_data) for poll_data in self._polls.values()]

storage = FileStorage()