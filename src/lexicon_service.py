"""
Lexicon & Pronunciation Service for Gemini TTS Studio
Allows users to define custom phonetic rules, acronym replacements, and pronunciation
corrections (e.g. 'SQL' -> 'Es-Kju-Ell', 'ChatGPT' -> 'Tschätt-Dschi-Pi-Ti') before
sending text to the Gemini TTS engine.
"""

import json
import re
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional

from .config import APP_DATA_DIR, BASE_DIR

LEXICON_FILE = APP_DATA_DIR / "custom_lexicon.json"

# Default starter lexicon entries for common tech terms and abbreviations in German
DEFAULT_LEXICON_ENTRIES = [
    {
        "id": "def-sql",
        "term": "SQL",
        "replacement": "Es-Kju-Ell",
        "type": "akronym",
        "case_sensitive": False,
        "is_regex": False,
        "enabled": True,
    },
    {
        "id": "def-chatgpt",
        "term": "ChatGPT",
        "replacement": "Tschätt-Dschi-Pi-Ti",
        "type": "eigenname",
        "case_sensitive": False,
        "is_regex": False,
        "enabled": True,
    },
    {
        "id": "def-dr",
        "term": "Dr.",
        "replacement": "Doktor",
        "type": "abkuerzung",
        "case_sensitive": True,
        "is_regex": False,
        "enabled": True,
    },
    {
        "id": "def-prof",
        "term": "Prof.",
        "replacement": "Professor",
        "type": "abkuerzung",
        "case_sensitive": True,
        "is_regex": False,
        "enabled": True,
    },
    {
        "id": "def-kmh",
        "term": r"\b(\d+)\s*km/h\b",
        "replacement": r"\1 Kilometer pro Stunde",
        "type": "regex",
        "case_sensitive": False,
        "is_regex": True,
        "enabled": True,
    },
]


def load_lexicon() -> List[Dict[str, Any]]:
    """Load all lexicon rules from custom_lexicon.json or initialize defaults."""
    if LEXICON_FILE.exists():
        try:
            with open(LEXICON_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception as e:
            print(f"Hinweis beim Laden des Aussprache-Lexikons: {e}")
    
    # Check fallback in BASE_DIR
    fallback = BASE_DIR / "custom_lexicon.json"
    if fallback.exists():
        try:
            with open(fallback, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass

    # Save and return defaults
    save_lexicon(DEFAULT_LEXICON_ENTRIES)
    return DEFAULT_LEXICON_ENTRIES


def save_lexicon(rules: List[Dict[str, Any]]) -> bool:
    """Save lexicon rules to disk."""
    try:
        LEXICON_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LEXICON_FILE, "w", encoding="utf-8") as f:
            json.dump(rules, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Fehler beim Speichern des Aussprache-Lexikons: {e}")
        # Try fallback in BASE_DIR
        try:
            fallback = BASE_DIR / "custom_lexicon.json"
            with open(fallback, "w", encoding="utf-8") as f:
                json.dump(rules, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False


def reset_lexicon_to_defaults() -> List[Dict[str, Any]]:
    """Reset lexicon to factory default starter rules and persist."""
    save_lexicon(DEFAULT_LEXICON_ENTRIES)
    return list(DEFAULT_LEXICON_ENTRIES)


def add_lexicon_entry(term: str, replacement: str, entry_type: str = "benutzer",
                      case_sensitive: bool = False, is_regex: bool = False) -> Dict[str, Any]:
    """Add a new entry to the lexicon and persist."""
    rules = load_lexicon()
    new_entry = {
        "id": str(uuid.uuid4())[:8],
        "term": term.strip(),
        "replacement": replacement.strip(),
        "type": entry_type,
        "case_sensitive": case_sensitive,
        "is_regex": is_regex,
        "enabled": True,
    }
    rules.append(new_entry)
    save_lexicon(rules)
    return new_entry


def update_lexicon_entry(entry_id: str, **kwargs) -> bool:
    """Update fields of an existing lexicon entry."""
    rules = load_lexicon()
    for entry in rules:
        if entry.get("id") == entry_id:
            entry.update(kwargs)
            return save_lexicon(rules)
    return False


def delete_lexicon_entry(entry_id: str) -> bool:
    """Delete a lexicon entry by ID."""
    rules = load_lexicon()
    new_rules = [e for e in rules if e.get("id") != entry_id]
    if len(new_rules) != len(rules):
        return save_lexicon(new_rules)
    return False


def apply_lexicon(text: str, rules: Optional[List[Dict[str, Any]]] = None) -> str:
    """
    Applies all active phonetic lexicon replacements to the given text,
    preserving directives and audio tags intact.
    """
    if not text:
        return text

    if rules is None:
        rules = load_lexicon()

    processed_text = text

    for rule in rules:
        if not rule.get("enabled", True):
            continue

        term = rule.get("term", "").strip()
        replacement = rule.get("replacement", "")
        if not term:
            continue

        is_regex = rule.get("is_regex", False)
        case_sensitive = rule.get("case_sensitive", False)
        flags = 0 if case_sensitive else re.IGNORECASE

        try:
            if is_regex:
                # Direct regex substitution
                processed_text = re.sub(term, replacement, processed_text, flags=flags)
            else:
                # Word-boundary matching for regular words/acronyms to avoid substring collisions
                escaped = re.escape(term)
                # If term starts/ends with alphanumeric, enforce word boundary
                pattern = r""
                if term[0].isalnum():
                    pattern += r"\b"
                pattern += escaped
                if term[-1].isalnum():
                    pattern += r"\b"

                processed_text = re.sub(pattern, replacement, processed_text, flags=flags)
        except re.error as e:
            print(f"Warnung: Ungültiges Regex im Aussprache-Lexikon ('{term}'): {e}")

    return processed_text
