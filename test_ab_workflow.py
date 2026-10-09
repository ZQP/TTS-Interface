"""
Unit test for Smart A/B Comparison and Decoupled History Dialog
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# Ensure src is in python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.history_service import log_generation, load_history, clear_history
from src.gui import GeminiTTSApp, HistoryDialog

def test_history_service_flow():
    print("=== Testing History Service Flow ===")
    clear_history()
    assert len(load_history()) == 0, "History should be empty"

    dummy_audio = Path("test_dummy.wav")
    dummy_audio.touch()

    take1 = log_generation(dummy_audio, "Fenrir", "gemini-3.8-flash-tts", "Dies ist ein Test für Stimme A.", duration_sec=3.5)
    take2 = log_generation(dummy_audio, "Puck", "gemini-3.8-flash-tts", "Dies ist ein Test für Stimme B.", duration_sec=3.8)

    history = load_history()
    assert len(history) == 2, f"Expected 2 takes, got {len(history)}"
    assert history[0]["voice"] == "Puck"
    assert history[1]["voice"] == "Fenrir"
    print("[+] History service correctly logs and orders takes!")

    clear_history()
    assert len(load_history()) == 0, "History should be empty after clear"
    if dummy_audio.exists():
        dummy_audio.unlink()
    print("[+] Clear history working properly!")

def test_ab_smart_delta_state():
    print("=== Testing GUI Smart A/B Logic & Delta Caching ===")
    import tkinter.messagebox as mb
    mb.showinfo = lambda *args, **kwargs: None
    mb.showwarning = lambda *args, **kwargs: None
    mb.showerror = lambda *args, **kwargs: None

    app = GeminiTTSApp()
    app.withdraw()

    # 1. Initially without text or generation
    app.text_input.delete("0.0", "end")
    app.text_input.insert("0.0", "Hallo Welt, dies ist ein A/B Test.")
    app.ab_voice_a_var.set("Fenrir (Männlich)")
    app.ab_voice_b_var.set("Puck (Männlich)")
    app._update_ab_status_labels()

    assert "Noch nicht generiert" in app.ab_status_a_lbl.cget("text")
    assert "Wartet auf Generierung" in app.ab_status_b_lbl.cget("text")
    assert "Beide Varianten generieren" in app.btn_ab_generate.cget("text")
    print("[+] State 1 (Both missing): Button is 'Beide Varianten generieren'")

    import wave
    def create_dummy_wav(path: Path):
        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(b"\x00\x00" * 2400)

    # 2. Simulate Variant A being generated for current text
    fake_wav_a = Path("test_fake_a.wav")
    create_dummy_wav(fake_wav_a)
    app.current_generated_wav = fake_wav_a
    app.current_generated_text = "Hallo Welt, dies ist ein A/B Test."
    app.voice_var.set("Fenrir (Männlich)")
    app._update_ab_status_labels()

    assert "Bereits generiert" in app.ab_status_a_lbl.cget("text")
    assert "Nur noch Variante B generieren" in app.btn_ab_generate.cget("text")
    assert "Beide neu generieren" in app.btn_ab_generate_both.cget("text")
    print("[+] State 2 (Variant A cached): Smart CTA is 'Nur noch Variante B generieren' + 'Beide neu generieren'!")

    # 2b. Test that changing the text in input invalidates Variant A!
    app.text_input.delete("0.0", "end")
    app.text_input.insert("0.0", "Ein völlig neuer Text, der noch nicht vertont wurde.")
    app._update_ab_status_labels()
    assert "Noch nicht generiert" in app.ab_status_a_lbl.cget("text")
    assert "Beide Varianten generieren" in app.btn_ab_generate.cget("text")
    print("[+] State 2b (Text mismatch): Variant A invalidated, CTA offers generating BOTH tracks!")

    # Revert text for step 3
    app.text_input.delete("0.0", "end")
    app.text_input.insert("0.0", "Hallo Welt, dies ist ein A/B Test.")
    app._update_ab_status_labels()

    # 3. Simulate Variant B also cached
    fake_wav_b = Path("test_fake_b.wav")
    create_dummy_wav(fake_wav_b)
    app.ab_cached_b = {
        "text": "Hallo Welt, dies ist ein A/B Test.",
        "voice": "Puck",
        "voice_label": "Puck (Männlich)",
        "wav": fake_wav_b,
        "converted": fake_wav_b,
        "duration": 0.1
    }
    app._update_ab_status_labels()

    assert "Bereits generiert" in app.ab_status_b_lbl.cget("text")
    assert "erneut generieren" in app.btn_ab_generate.cget("text")
    print("[+] State 3 (Both cached): Smart CTA is 'Beide Varianten erneut generieren'!")

    # 4. Test Adopting Variant B
    app._adopt_ab_variant("B")
    assert app.current_generated_wav == fake_wav_b
    assert app.current_generated_text == "Hallo Welt, dies ist ein A/B Test."
    assert app.voice_var.get() == "Puck (Männlich)"
    print("[+] State 4 (Adopt Variant B): Main player, text tracking and voice dropdown updated to Puck!")

    # 5. Clean up fake files & app
    try:
        import pygame
        pygame.mixer.music.unload()
    except Exception:
        pass
    if fake_wav_a.exists():
        try:
            fake_wav_a.unlink()
        except Exception:
            pass
    if fake_wav_b.exists():
        try:
            fake_wav_b.unlink()
        except Exception:
            pass
    app.destroy()
    print("[+] All Smart A/B unit tests passed with 100% success!")

if __name__ == "__main__":
    test_history_service_flow()
    test_ab_smart_delta_state()
