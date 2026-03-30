import json
import os

DEFAULT_CONFIG = {
    "break_interval_min": 45,
    "slime_position": None,
    "reminders": [],
    "always_on_top": True,
    "size_percent": 100,
}


class Settings:
    def __init__(self, path="config.json"):
        self._path = path
        self.data = dict(DEFAULT_CONFIG)
        self.load()

    def load(self):
        if os.path.exists(self._path):
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                self.data.update(saved)
            except (json.JSONDecodeError, IOError):
                pass

    def save(self):
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except IOError:
            pass

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()
