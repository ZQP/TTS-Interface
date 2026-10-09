"""
Subtitle & Video Synchronization Service for Gemini TTS Studio
Generates, edits, synchronizes and exports frame-accurate .srt and .vtt subtitles
matching speech audio synthesized by Gemini.
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional


def clean_subtitle_text(text: str) -> str:
    """
    Strips internal TTS directives, emotion cues, and non-verbal tags
    so only clean, readable spoken text remains for subtitles.
    """
    if not text:
        return ""

    cleaned = text
    # Remove [Tone: ...] directives
    cleaned = re.sub(r"\[Tone:\s*[^\]]+\]", "", cleaned, flags=re.IGNORECASE)
    # Remove XML-style audio cues like <laughs>, <sigh>, <gasp>, <throat-clearing>
    cleaned = re.sub(r"<[^>]+>", "", cleaned)
    # Remove bracketed tags like [lachen], [flüstert], [flüstern], [pause], [whisper]
    cleaned = re.sub(r"\[(?:lachen|lacht|lachend|flüstern|flüstert|flüsternd|pause|seufzen|seufzt|gähnen|husten|räuspern|whisper|whispering|laugh|laughing|sigh|sighing|gasp|cough)\]", "", cleaned, flags=re.IGNORECASE)
    # Remove verbal fillers like |mhm|
    cleaned = re.sub(r"\|[^\|]+\|", "", cleaned)
    # Normalize extra whitespaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def format_timestamp_srt(seconds: float) -> str:
    """Format seconds into SRT timestamp format: HH:MM:SS,mmm"""
    if seconds < 0:
        seconds = 0
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000:
        secs += 1
        millis = 0
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"


def format_timestamp_vtt(seconds: float) -> str:
    """Format seconds into WebVTT timestamp format: HH:MM:SS.mmm"""
    if seconds < 0:
        seconds = 0
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000:
        secs += 1
        millis = 0
    return f"{hrs:02d}:{mins:02d}:{secs:02d}.{millis:03d}"


def parse_timestamp(timestamp_str: str) -> float:
    """Parse SRT or VTT timestamp string into seconds float."""
    ts = timestamp_str.strip().replace(",", ".")
    parts = ts.split(":")
    if len(parts) == 3:
        hrs, mins, secs = parts
        return float(hrs) * 3600 + float(mins) * 60 + float(secs)
    elif len(parts) == 2:
        mins, secs = parts
        return float(mins) * 60 + float(secs)
    try:
        return float(ts)
    except ValueError:
        return 0.0


class SubtitleCue:
    """Represents an individual subtitle cue block."""

    def __init__(self, index: int, start_time: float, end_time: float, text: str):
        self.index = index
        self.start_time = max(0.0, start_time)
        self.end_time = max(self.start_time + 0.1, end_time)
        self.text = text.strip()

    @property
    def duration(self) -> float:
        return round(self.end_time - self.start_time, 3)

    @property
    def chars_per_second(self) -> float:
        if self.duration <= 0:
            return 0.0
        return round(len(self.text) / self.duration, 1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "start_srt": format_timestamp_srt(self.start_time),
            "end_srt": format_timestamp_srt(self.end_time),
            "duration": self.duration,
            "text": self.text,
            "cps": self.chars_per_second,
        }

    def to_srt_block(self) -> str:
        start_str = format_timestamp_srt(self.start_time)
        end_str = format_timestamp_srt(self.end_time)
        return f"{self.index}\n{start_str} --> {end_str}\n{self.text}\n"

    def to_vtt_block(self) -> str:
        start_str = format_timestamp_vtt(self.start_time)
        end_str = format_timestamp_vtt(self.end_time)
        return f"{self.index}\n{start_str} --> {end_str}\n{self.text}\n"


def generate_cues_from_text_and_duration(
    text: str,
    total_duration: float,
    max_chars_per_line: int = 42,
    strip_tags: bool = True
) -> List[SubtitleCue]:
    """
    Intelligently segments text into sentence/phrase blocks and computes
    accurate timecodes proportional to text length across total_duration.
    """
    if not text or total_duration <= 0:
        return []

    # 1. Split into natural sentence/clause units
    # Regex splits by sentence endings followed by space, or linebreaks
    raw_sentences = re.split(r'(?<=[.!?…])\s+|\n+', text.strip())
    raw_sentences = [s.strip() for s in raw_sentences if s.strip()]

    if not raw_sentences:
        return []

    # 2. Further split overly long sentences exceeding max_chars_per_line
    segments: List[str] = []
    for s in raw_sentences:
        cleaned_s = clean_subtitle_text(s) if strip_tags else s
        if not cleaned_s:
            continue
        if len(cleaned_s) <= max_chars_per_line * 2:
            segments.append(cleaned_s)
        else:
            # Split at comma or conjunction
            sub_clauses = re.split(r'(?<=[,;:])\s+', cleaned_s)
            for clause in sub_clauses:
                if clause.strip():
                    segments.append(clause.strip())

    if not segments:
        return []

    # 3. Calculate time distribution based on character weight
    char_counts = [max(1, len(re.sub(r'\s+', '', seg))) for seg in segments]
    total_chars = sum(char_counts)

    # Allow slight silence margin at start and end
    intro_pause = min(0.3, total_duration * 0.05)
    usable_duration = total_duration - intro_pause
    inter_cue_gap = 0.15  # 150ms natural gap between subtitle lines

    cues: List[SubtitleCue] = []
    current_time = intro_pause

    for i, (seg, chars) in enumerate(zip(segments, char_counts)):
        weight = chars / total_chars
        segment_duration = usable_duration * weight
        # Ensure minimum duration of 1.2s and maximum duration proportional
        cue_dur = max(1.0, segment_duration - inter_cue_gap)
        start_t = current_time
        end_t = min(total_duration, start_t + cue_dur)

        cues.append(SubtitleCue(
            index=i + 1,
            start_time=round(start_t, 3),
            end_time=round(end_t, 3),
            text=seg
        ))
        current_time = end_t + inter_cue_gap

    # Ensure last cue does not exceed total_duration
    if cues and cues[-1].end_time > total_duration:
        cues[-1].end_time = total_duration

    return cues


def export_srt_file(cues: List[SubtitleCue], output_path: Path) -> Path:
    """Exports a list of SubtitleCue objects to a .srt file with UTF-8 encoding."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(cue.to_srt_block() for cue in cues)
    output_path.write_text(content.strip() + "\n", encoding="utf-8")
    return output_path


def export_vtt_file(cues: List[SubtitleCue], output_path: Path) -> Path:
    """Exports a list of SubtitleCue objects to a .vtt file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    header = "WEBVTT - Generated by Gemini TTS Studio\n\n"
    content = "\n".join(cue.to_vtt_block() for cue in cues)
    output_path.write_text(header + content.strip() + "\n", encoding="utf-8")
    return output_path


def parse_srt_content(srt_text: str) -> List[SubtitleCue]:
    """Parses existing SRT text format into SubtitleCue objects."""
    cues = []
    blocks = re.split(r'\n\s*\n', srt_text.strip())
    pattern = re.compile(r'(\d+)\s*\n([\d:,]+)\s*-->\s*([\d:,]+)\s*\n([\s\S]+)')

    for block in blocks:
        match = pattern.match(block.strip())
        if match:
            idx = int(match.group(1))
            start_sec = parse_timestamp(match.group(2))
            end_sec = parse_timestamp(match.group(3))
    return cues


def generate_subtitle_cues(text: str, total_audio_duration_sec: float = 10.0) -> List[Dict[str, Any]]:
    """Generates subtitle cues dictionary format for UI tables and export."""
    cues = generate_cues_from_text_and_duration(text, total_audio_duration_sec)
    res = []
    for c in cues:
        d = c.to_dict()
        d["start"] = d.get("start_srt", format_timestamp_srt(c.start_time))
        d["end"] = d.get("end_srt", format_timestamp_srt(c.end_time))
        res.append(d)
    return res


def calculate_cps(text: str, duration: float) -> float:
    """Calculates Characters Per Second (CPS) rate for a given text snippet."""
    if duration <= 0:
        return 0.0
    return round(len(text) / duration, 1)


def cues_to_srt(cues: List[Any], output_path: Path) -> Path:
    """Exports list of cue dicts or SubtitleCue objects to .srt."""
    subtitle_cues = []
    for idx, c in enumerate(cues):
        if isinstance(c, SubtitleCue):
            subtitle_cues.append(c)
        elif isinstance(c, dict):
            s_val = c.get("start") or c.get("start_time") or 0
            e_val = c.get("end") or c.get("end_time") or 0
            s_sec = parse_timestamp(str(s_val)) if isinstance(s_val, str) else float(s_val)
            e_sec = parse_timestamp(str(e_val)) if isinstance(e_val, str) else float(e_val)
            subtitle_cues.append(SubtitleCue(
                index=c.get("index", idx + 1),
                start_time=s_sec,
                end_time=e_sec,
                text=c.get("text", "")
            ))
    return export_srt_file(subtitle_cues, output_path)


def cues_to_vtt(cues: List[Any], output_path: Path) -> Path:
    """Exports list of cue dicts or SubtitleCue objects to .vtt."""
    subtitle_cues = []
    for idx, c in enumerate(cues):
        if isinstance(c, SubtitleCue):
            subtitle_cues.append(c)
        elif isinstance(c, dict):
            s_val = c.get("start") or c.get("start_time") or 0
            e_val = c.get("end") or c.get("end_time") or 0
            s_sec = parse_timestamp(str(s_val)) if isinstance(s_val, str) else float(s_val)
            e_sec = parse_timestamp(str(e_val)) if isinstance(e_val, str) else float(e_val)
            subtitle_cues.append(SubtitleCue(
                index=c.get("index", idx + 1),
                start_time=s_sec,
                end_time=e_sec,
                text=c.get("text", "")
            ))
    return export_vtt_file(subtitle_cues, output_path)


def parse_srt(srt_text: str) -> List[Dict[str, Any]]:
    """Parses SRT format string into list of cue dictionaries."""
    cues = parse_srt_content(srt_text)
    res = []
    for c in cues:
        d = c.to_dict()
        d["start"] = d.get("start_srt", format_timestamp_srt(c.start_time))
        d["end"] = d.get("end_srt", format_timestamp_srt(c.end_time))
        res.append(d)
    return res

