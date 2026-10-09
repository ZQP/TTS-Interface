"""
Generation History & A/B Comparison State Manager for Gemini TTS Studio
Keeps a persistent log of synthesized audio takes, enabling quick A/B comparisons,
re-listening, and variant evaluation.
"""

import json
import time
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional

from .config import APP_DATA_DIR, BASE_DIR

HISTORY_FILE = APP_DATA_DIR / "generation_history.json"
MAX_HISTORY_ITEMS = 25

_CURRENT_SLOT_A_ID: Optional[str] = None
_CURRENT_SLOT_B_ID: Optional[str] = None


def load_history() -> List[Dict[str, Any]]:
    """Loads generation takes from disk."""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    # Filter for files that still exist or keep valid records
                    return data
        except Exception as e:
            print(f"Hinweis beim Laden der Historie: {e}")

    fallback = BASE_DIR / "generation_history.json"
    if fallback.exists():
        try:
            with open(fallback, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass

    return []


def save_history(history_items: List[Dict[str, Any]]) -> bool:
    """Saves history items to disk, capped to MAX_HISTORY_ITEMS."""
    try:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        # Cap
        capped = history_items[:MAX_HISTORY_ITEMS]
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(capped, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Fehler beim Speichern der Historie: {e}")
        try:
            fallback = BASE_DIR / "generation_history.json"
            with open(fallback, "w", encoding="utf-8") as f:
                json.dump(history_items[:MAX_HISTORY_ITEMS], f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False


def log_generation(
    audio_path: Path,
    voice_name: str,
    model: str,
    text: str,
    tone: Optional[str] = None,
    duration_sec: float = 0.0
) -> Dict[str, Any]:
    """Adds a newly synthesized audio take to the generation history."""
    audio_path = Path(audio_path).resolve()
    history = load_history()

    now = time.strftime("%H:%M:%S")
    now_date = time.strftime("%Y-%m-%d %H:%M")
    take_id = f"take-{int(time.time()*1000)}-{uuid.uuid4().hex[:6]}"

    snippet = (text or "").strip()
    if len(snippet) > 75:
        snippet = snippet[:72] + "..."

    item = {
        "id": take_id,
        "timestamp": now,
        "datetime": now_date,
        "audio_path": str(audio_path),
        "voice": voice_name,
        "model": model,
        "tone": tone or "Standard",
        "snippet": snippet,
        "duration": round(duration_sec, 2),
    }

    # Prepend new item to the top
    history.insert(0, item)
    save_history(history)

    # Automatically set Slot A to this newest take if Slot A is unset
    global _CURRENT_SLOT_A_ID
    if not _CURRENT_SLOT_A_ID:
        _CURRENT_SLOT_A_ID = take_id

    return item


def clear_history() -> bool:
    """Clears all history records."""
    global _CURRENT_SLOT_A_ID, _CURRENT_SLOT_B_ID
    _CURRENT_SLOT_A_ID = None
    _CURRENT_SLOT_B_ID = None
    return save_history([])


def get_take_by_id(take_id: str) -> Optional[Dict[str, Any]]:
    """Finds a specific take record by ID."""
    history = load_history()
    for item in history:
        if item.get("id") == take_id:
            return item
    return None


def set_ab_slot(slot: str, take_id: str):
    """Assigns a take to Slot A or Slot B."""
    global _CURRENT_SLOT_A_ID, _CURRENT_SLOT_B_ID
    if slot.upper() == "A":
        _CURRENT_SLOT_A_ID = take_id
    elif slot.upper() == "B":
        _CURRENT_SLOT_B_ID = take_id


def get_ab_slots() -> Dict[str, Optional[Dict[str, Any]]]:
    """Returns currently selected records for Slot A and Slot B."""
    global _CURRENT_SLOT_A_ID, _CURRENT_SLOT_B_ID
    history = load_history()

    take_a = None
    take_b = None

    if _CURRENT_SLOT_A_ID:
        take_a = get_take_by_id(_CURRENT_SLOT_A_ID)
    elif len(history) > 0:
        take_a = history[0]
        _CURRENT_SLOT_A_ID = take_a["id"]

    if _CURRENT_SLOT_B_ID:
        take_b = get_take_by_id(_CURRENT_SLOT_B_ID)
    elif len(history) > 1:
        take_b = history[1]
        _CURRENT_SLOT_B_ID = take_b["id"]

    return {
        "A": take_a,
        "B": take_b,
    }
