"""
Comprehensive Headless Unit Tests for Gemini TTS Studio v3.0.0 Features:
1. Phonetic Lexicon & Pronunciation Correction
2. Subtitles & SRT/VTT Generation & Tag Filtering
3. Multi-Speaker & Dialogue Script Parsing
4. Generation History & A/B Comparison Slots
5. Audio Ducking Module & FFmpeg Validation
"""

import sys
from pathlib import Path

# Ensure root directory is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.lexicon_service import (
    apply_lexicon,
    add_lexicon_entry,
    load_lexicon,
    save_lexicon,
    update_lexicon_entry,
    delete_lexicon_entry,
    reset_lexicon_to_defaults
)
from src.subtitle_service import (
    clean_subtitle_text,
    generate_cues_from_text_and_duration,
    generate_subtitle_cues,
    calculate_cps,
    cues_to_srt,
    cues_to_vtt,
    parse_srt,
    export_srt_file,
    export_vtt_file,
    format_timestamp_srt,
    format_timestamp_vtt
)
from src.script_processor import (
    parse_script,
    extract_unique_speakers,
    extract_speakers,
    synthesize_dialogue_script
)
from src.history_service import log_generation, get_ab_slots, set_ab_slot, load_history, clear_history
from src.audio_ducking import apply_audio_ducking
from src.audio_converter import get_ffmpeg_path


TEMP_TEST_DIR = Path("temp")
TEMP_TEST_DIR.mkdir(exist_ok=True)


def test_lexicon():
    print("=== 1. Testing Phonetic Lexicon Service ===")
    test_text = "Dr. Weber analysiert die SQL-Datenbank und ChatGPT bei 130 km/h."
    transformed = apply_lexicon(test_text)
    print("  Original:   ", test_text)
    print("  Transformed:", transformed)

    assert "Doktor" in transformed, "Dr. should be replaced with Doktor"
    assert "Es-Kju-Ell" in transformed, "SQL should be replaced with Es-Kju-Ell"
    assert "Tschätt-Dschi-Pi-Ti" in transformed, "ChatGPT should be replaced"
    assert "Kilometer pro Stunde" in transformed, "km/h regex should be replaced"
    print("  [+] Phonetic Lexicon test PASSED successfully!\n")


def test_subtitles():
    print("=== 2. Testing Subtitle & SRT/VTT Service ===")
    # 2.1 Tag cleaning
    dirty_text = "Hallo! <laughs> Das ist ein Test. [flüstert] Alles funktioniert [pause] wunderbar! |mhm| [Tone: Begeistert]"
    cleaned = clean_subtitle_text(dirty_text)
    print("  Original text: ", dirty_text)
    print("  Cleaned for SRT:", cleaned)
    assert "<laughs>" not in cleaned
    assert "[flüstert]" not in cleaned
    assert "[pause]" not in cleaned
    assert "|mhm|" not in cleaned
    assert "[Tone:" not in cleaned
    assert "Hallo! Das ist ein Test. Alles funktioniert wunderbar!" == cleaned

    # 2.2 Cue generation and timing
    sample_speech = "Guten Tag! Willkommen zu Gemini TTS Studio. Heute testen wir den präzisen Export von Untertiteln."
    cues = generate_cues_from_text_and_duration(sample_speech, total_duration=10.0)
    print(f"  Generated {len(cues)} cues for {10.0}s duration:")
    for cue in cues:
        print(f"    - Cue #{cue.index}: [{cue.to_dict()['start_srt']} --> {cue.to_dict()['end_srt']}] ({cue.duration}s, {cue.chars_per_second} CPS): '{cue.text}'")

    assert len(cues) == 3, f"Expected 3 sentence cues, got {len(cues)}"
    assert cues[0].start_time >= 0.0
    assert cues[-1].end_time <= 10.0

    # 2.3 SRT & VTT export
    srt_out = TEMP_TEST_DIR / "test_subs.srt"
    vtt_out = TEMP_TEST_DIR / "test_subs.vtt"
    export_srt_file(cues, srt_out)
    export_vtt_file(cues, vtt_out)

    assert srt_out.exists() and srt_out.stat().st_size > 0
    assert vtt_out.exists() and vtt_out.stat().st_size > 0
    print(f"  [+] Exported SRT ({srt_out.stat().st_size} bytes) and VTT ({vtt_out.stat().st_size} bytes)")
    print("  [+] Subtitle service tests PASSED successfully!\n")


def test_script_processor():
    print("=== 3. Testing Multi-Speaker Script Processor ===")
    sample_script = """
[Erzähler]: Es war ein kühler Oktoberabend im Labor von Professor Weber.
[Weber]: (aufgeregt) Endlich! Nach drei Jahren intensiver Forschung spricht das System vollkommen natürlich! <laughs>
[Assistent]: (zögernd) Aber Professor... haben Sie auch an die Sicherheitsrichtlinien gedacht?
[Weber]: Vergiss die Richtlinien! Wir schreiben Geschichte!
"""
    turns = parse_script(sample_script)
    speakers = extract_unique_speakers(sample_script)

    print(f"  Discovered {len(speakers)} unique speakers: {speakers}")
    assert speakers == ["Erzähler", "Weber", "Assistent"]
    assert len(turns) == 4, f"Expected 4 turns, got {len(turns)}"

    print("  Dialogue turns parsed:")
    for t in turns:
        print(f"    - [{t.speaker}] (Hint: '{t.emotion_hint}'): '{t.text[:40]}...'")

    assert turns[1].speaker == "Weber"
    assert turns[1].emotion_hint == "aufgeregt"
    assert turns[2].speaker == "Assistent"
    assert turns[2].emotion_hint == "zögernd"
    print("  [+] Script processor tests PASSED successfully!\n")


def test_history_and_ab():
    print("=== 4. Testing History & A/B Comparison Service ===")
    clear_history()
    fake_audio = TEMP_TEST_DIR / "dummy_take.wav"
    fake_audio.write_text("RIFFfake", encoding="utf-8")

    item1 = log_generation(fake_audio, voice_name="Erinome", model="Gemini 3.8 Flash", text="Hallo Variante A", tone="Natürlich", duration_sec=3.5)
    item2 = log_generation(fake_audio, voice_name="Puck", model="Gemini 3.8 Flash Lite", text="Hallo Variante B", tone="Dynamisch", duration_sec=3.2)

    set_ab_slot("A", item1["id"])
    set_ab_slot("B", item2["id"])

    slots = get_ab_slots()
    print(f"  Slot A: {slots['A']['voice']} ({slots['A']['id']})")
    print(f"  Slot B: {slots['B']['voice']} ({slots['B']['id']})")

    assert slots["A"]["id"] == item1["id"]
    assert slots["B"]["id"] == item2["id"]
    assert slots["A"]["voice"] == "Erinome"
    assert slots["B"]["voice"] == "Puck"
    print("  [+] History & A/B Comparison tests PASSED successfully!\n")


def test_ffmpeg():
    print("=== 5. Testing FFmpeg Location for Audio Ducking ===")
    ffmpeg_path = get_ffmpeg_path()
    print("  FFmpeg binary path:", ffmpeg_path)
    assert Path(ffmpeg_path).exists(), f"FFmpeg binary not found at {ffmpeg_path}"
    print("  [+] FFmpeg path verification PASSED successfully!\n")


def test_gui_and_main_imports():
    print("=== 6. Testing Full GUI & Application Imports ===")
    from src.gui import GeminiTTSApp, LexiconDialog, SubtitleStudioDialog, SettingsDialog
    import main
    print("  [+] Successfully imported GeminiTTSApp, LexiconDialog, SubtitleStudioDialog, SettingsDialog and main.py!")
    print("  [+] GUI & Application import test PASSED successfully!\n")


def test_audio_conversion_and_paths():
    print("=== 7. Testing Audio Conversion and Output Paths ===")
    from src.config import get_output_dir
    from src.audio_converter import convert_audio, get_ffmpeg_path
    import subprocess
    
    out_dir = get_output_dir()
    assert out_dir.exists(), f"Output directory {out_dir} does not exist"
    
    dummy_wav = TEMP_TEST_DIR / "test_synth.wav"
    subprocess.run([get_ffmpeg_path(), "-y", "-f", "lavfi", "-i", "sine=frequency=1000:duration=1", dummy_wav.as_posix()], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    target_m4a = out_dir / "test_verify_302.m4a"
    res = convert_audio(dummy_wav, target_m4a, codec="aac", channels=1, sample_rate=44100, bitrate="64k", faststart=True)
    assert res.exists() and res.stat().st_size > 0
    print(f"  [+] Successfully converted test audio to {res.name} ({res.stat().st_size} bytes)")
    if target_m4a.exists():
        try:
            target_m4a.unlink()
        except Exception:
            pass
    print("  [+] Audio conversion and paths test PASSED successfully!\n")


if __name__ == "__main__":
    print("=======================================================")
    print("=== RUNNING GEMINI TTS STUDIO FEATURE TESTS ===")
    print("=======================================================\n")
    test_lexicon()
    test_subtitles()
    test_script_processor()
    test_history_and_ab()
    test_ffmpeg()
    test_gui_and_main_imports()
    test_audio_conversion_and_paths()
    print("=======================================================")
    print("[+] ALL TESTS COMPLETED 100% OK!")
    print("=======================================================")

