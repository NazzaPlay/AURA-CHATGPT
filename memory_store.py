import json
import os
from typing import Any


def load_memory(memory_file: str) -> dict[str, Any]:
    if os.path.exists(memory_file):
        try:
            with open(memory_file, "r", encoding="utf-8") as f:
                loaded = json.load(f)
        except (OSError, json.JSONDecodeError):
            return {}
        if isinstance(loaded, dict):
            return loaded
    return {}


def save_memory(memory: dict[str, Any], memory_file: str) -> None:
    os.makedirs(os.path.dirname(memory_file) or ".", exist_ok=True)
    with open(memory_file, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2, ensure_ascii=False)
