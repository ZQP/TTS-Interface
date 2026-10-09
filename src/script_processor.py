"""
Multi-Speaker & Script Processor for Gemini TTS Studio
Parses dialogue scripts and radio plays (e.g. '[Erzähler]: ...', '[Puck]: ...'),
manages speaker cast assignments, and orchestrates multi-voice synthesis
with seamless audio stitching.
"""

import re
import wave
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Tuple

from .config import TEMP_DIR
from .tts_service import GeminiTTSService


class ScriptLine:
    """Represents a single dialogue turn in a multi-speaker script."""

    def __init__(self, speaker: str, text: str, emotion_hint: str = ""):
        self.speaker = speaker.strip()
        self.text = text.strip()
        self.emotion_hint = emotion_hint.strip()

    def __repr__(self):
        return f"<ScriptLine speaker='{self.speaker}' chars={len(self.text)} hint='{self.emotion_hint}'>"


# Regex patterns to detect speaker prefixes:
# 1. Bracketed format: "[Erzähler]: Guten Tag", "[Puck]: Hallo!"
# 2. Parenthesized hint format: "[Weber]: (aufgeregt) Endlich!"
# 3. Colon format: "Erzähler: Guten Tag"
SPEAKER_PREFIX_PATTERN = re.compile(
    r"^(?:\[([^\]]+)\]|([A-Za-zÄÖÜäöüß0-9_\-\s]{2,25}))\s*:\s*(?:(?:\(([^\)]+)\)|\[([^\]]+)\])\s*)?(.*)$",
    re.MULTILINE
)


def parse_script(script_text: str) -> List[ScriptLine]:
    """
    Parses a multi-speaker script into structured ScriptLine objects,
    extracting speaker names, inline emotional cues (e.g. '(flüstert)'),
    and the dialogue text.
    """
    if not script_text or not script_text.strip():
        return []

    lines = script_text.strip().split("\n")
    dialogue_turns: List[ScriptLine] = []

    current_speaker = "Erzähler"
    current_hint = ""
    current_buffer = []

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        # Check if line starts a new speaker turn
        match = re.match(r"^(?:\[([^\]]+)\]|([A-Za-zÄÖÜäöüß0-9_\-\.]{2,30}))\s*:\s*(?:(?:\(([^\)]+)\)|\[([^\]]+)\])\s*)?(.*)$", line)
        if match:
            # Flush previous speaker's accumulated dialogue if any
            if current_buffer:
                full_text = " ".join(current_buffer).strip()
                if full_text:
                    dialogue_turns.append(ScriptLine(current_speaker, full_text, current_hint))
                current_buffer = []

            # Extract new speaker
            speaker_name = match.group(1) or match.group(2) or "Sprecher"
            speaker_name = speaker_name.strip()

            # Extract inline parenthetical hint like (aufgeregt) or (flüstert)
            inline_hint = match.group(3) or match.group(4) or ""
            current_speaker = speaker_name
            current_hint = inline_hint.strip()

            dialogue_text = match.group(5) or ""
            if dialogue_text.strip():
                current_buffer.append(dialogue_text.strip())
        else:
            # Continuation line for the current speaker
            current_buffer.append(line)

    # Flush final turn
    if current_buffer:
        full_text = " ".join(current_buffer).strip()
        if full_text:
            dialogue_turns.append(ScriptLine(current_speaker, full_text, current_hint))

    return dialogue_turns


def extract_unique_speakers(script_text: str) -> List[str]:
    """Returns a list of all unique speaker names discovered in the script."""
    turns = parse_script(script_text)
    seen = []
    for turn in turns:
        if turn.speaker not in seen:
            seen.append(turn.speaker)
    return seen


def generate_multi_speaker_audio(
    script_text: str,
    cast_map: Dict[str, Dict[str, Any]],
    tts_service: GeminiTTSService,
    default_voice: str = "Erinome",
    default_model: Optional[str] = None,
    language: str = "de",
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    pause_between_speakers_ms: int = 350
) -> Path:
    """
    Synthesizes a multi-speaker script sequentially, switching voices and tones
    per speaker, and stitches the audio seamlessly into one master WAV file.
    
    cast_map format:
    {
        "Erzähler": {"voice": "Charon", "tone": "Ruhig und dokumentarisch"},
        "Puck": {"voice": "Puck", "tone": "Dynamisch, aufgeregt"},
    }
    """
    turns = parse_script(script_text)
    if not turns:
        raise ValueError("Das Skript enthält keinen lesbaren Dialog.")

    total_turns = len(turns)
    turn_pcm_frames = []
    sample_rate = 24000
    channels = 1
    sample_width = 2

    # Calculate silence gap frames between speakers
    gap_samples = int(sample_rate * (pause_between_speakers_ms / 1000.0))
    silence_gap = b"\x00" * (gap_samples * sample_width * channels)

    for i, turn in enumerate(turns):
        if progress_callback:
            progress_callback(i + 1, total_turns, f"Generiere Sprecher [{turn.speaker}] ({i+1}/{total_turns})...")

        # Determine speaker settings
        speaker_config = cast_map.get(turn.speaker, {})
        voice_name = speaker_config.get("voice", default_voice)
        base_tone = speaker_config.get("tone", "")

        # Merge base tone with inline emotion hint if present
        tone_directives = []
        if base_tone:
            tone_directives.append(base_tone)
        if turn.emotion_hint:
            tone_directives.append(turn.emotion_hint)
        system_instruction = ", ".join(tone_directives) if tone_directives else None

        # Synthesize speech for this turn
        turn_wav_path = tts_service.generate_speech(
            text=turn.text,
            voice_name=voice_name,
            model=default_model or "gemini-3.8-flash-tts",
            system_prompt=system_instruction,
            language=language
        )

        # Read PCM frames from the generated WAV
        with wave.open(str(turn_wav_path), "rb") as wf:
            sample_rate = wf.getframerate()
            channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            frames = wf.readframes(wf.getnframes())
            turn_pcm_frames.append(frames)

        # Cleanup temporary turn WAV
        try:
            turn_wav_path.unlink(missing_ok=True)
        except Exception:
            pass

    # Stitch all turns together into master WAV
    import time
    master_wav_path = TEMP_DIR / f"multispeaker_{int(time.time()*1000)}.wav"

    with wave.open(str(master_wav_path), "wb") as master_wf:
        master_wf.setnchannels(channels)
        master_wf.setsampwidth(sample_width)
        master_wf.setframerate(sample_rate)

        for idx, frames in enumerate(turn_pcm_frames):
            master_wf.writeframes(frames)
            # Add small natural pause between turns (except after the last turn)
            if idx < len(turn_pcm_frames) - 1 and pause_between_speakers_ms > 0:
                master_wf.writeframes(silence_gap)

    return master_wav_path


extract_speakers = extract_unique_speakers


def synthesize_dialogue_script(
    script_text: str,
    speaker_voice_map: Dict[str, str],
    pause_duration_ms: int = 350,
    progress_callback: Optional[Callable[[float, str], None]] = None,
    tts_service: Optional[GeminiTTSService] = None
) -> Path:
    """Convenience wrapper for synthesizing a dialogue script with speaker-to-voice mapping."""
    if tts_service is None:
        tts_service = GeminiTTSService()

    cast_map = {}
    for spk, v in speaker_voice_map.items():
        cast_map[spk] = {"voice": v}

    def adapter(cur: int, tot: int, msg: str):
        if progress_callback:
            frac = cur / max(1, tot)
            progress_callback(frac, msg)

    return generate_multi_speaker_audio(
        script_text=script_text,
        cast_map=cast_map,
        tts_service=tts_service,
        progress_callback=adapter,
        pause_between_speakers_ms=pause_duration_ms
    )

