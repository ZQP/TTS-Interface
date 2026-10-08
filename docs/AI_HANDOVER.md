# KI-Handover & Developer Guide

Dieses Dokument richtet sich an nachfolgende **KI-Agenten (Gemini, Claude, GPT, Cursor, Copilot etc.)** und menschliche Entwickler. Es fasst die Architektur, getroffenen Entscheidungen, bekannte Fallstricke und Erweiterungsmöglichkeiten zusammen.

---

## 1. Quick Start für KI-Agenten

1. **Repository-Zustand prüfen**:
   ```bash
   git status
   ```
2. **Abhängigkeiten installieren**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Tests ausführen**:
   ```bash
   python test_tts.py
   python test_batch.py
   ```
4. **App im Entwicklungsmodus starten**:
   ```bash
   python main.py
   ```
5. **Standalone Windows EXE bauen**:
   ```bash
   python build_exe.py
   ```

---

## 2. Wichtige Module & Verantwortlichkeiten

| Modul | Zweck |
| :--- | :--- |
| `src/document_parser.py` | Extrahiert Text aus `.txt`, `.md`, `.pdf` (`pypdf`), `.docx` (`python-docx`), `.srt` und splittet Kapitel anhand von Überschriften (`# Kapitel`). |
| `src/batch_processor.py` | Verwaltet die Warteschlange (`BatchItem`) für Stapelverarbeitung, unterstützt mehrsprachigen Export und sequentielle Generierung. |
| `src/translation_service.py` | Nutzt `gemini-3.8-flash` zur Übersetzung in bis zu 32 Zielsprachen bei striktem Erhalt aller eckigen Audio-Tags (`[lachen]`, `[Pause]`, etc.). |
| `src/tts_service.py` | Gemini API Client, Tag-Übersetzung (`[lachen]` $\to$ `[laugh]`), Smart Chunking gegen Timeouts, PCM-Stitching, Ton-Direktiven (`[Tone: ...]`) & Modell-Fallback. |
| `src/audio_converter.py` | FFmpeg-Wrapper für AAC-LC Mono 64k FastStart MP4/M4A/MP3 Konvertierung. |
| `src/player.py` | Pygame Audio Player mit Scrubbing-Unterstützung (`seek`). |
| `src/gui.py` | CustomTkinter GUI mit Modus-Umschaltung (Einzeltext / Batch), stabiler Zonen-Hierarchie, `AutoScrollableFrame` und Echtzeit-Status. |
| `src/config.py` | 18 verifizierte Stimmen, 32 Sprachen, Modelle, Presets, Pfade und `.env`-Management (auch im PyInstaller frozen Mode). |

---

## 3. Bekannte Fallstricke & API-Besonderheiten

- **Gemini TTS Preview Endpunkte**: `gemini-3.1-flash-tts-preview` und `gemini-2.5-flash-preview-tts` akzeptieren **keine** `systemInstruction` im Payload (wirft sonst API-Fehler `Developer instruction is not enabled for this model`). Regieanweisungen/Sprechstile werden jedoch nativ verarbeitet, wenn sie als `[Tone: ...]` am Anfang jedes Chunks mitgegeben werden. Das Modell liest diese nicht vor, sondern setzt sie als Sprechstil um!
- **Timeouts bei langen Texten**: Die Smart-Chunking-Engine in `src/tts_service.py` zerlegt Texte an Satzgrenzen in Blöcke à ~300 Zeichen und konkateniert die resultierenden PCM-Bytes nahtlos.
- **PyInstaller Bundling & Assets**: `build_exe.py` sammelt `--collect-all=customtkinter`, `--collect-all=imageio_ffmpeg`, `--collect-all=pygame`, `--collect-all=pypdf`, `--collect-all=docx`, bindet das neue App-Icon ein (`--icon=assets/icon.ico`) und kopiert Assets (`--add-data=assets;assets`).
- **Inno Setup Windows Installer**: `build_installer.py` und `installer.iss` erzeugen einen vollwertigen Windows-Installer (`dist/installer/GeminiTTSStudio-Setup-2.3.1.exe`) mit `PrivilegesRequired=lowest` (Installation in `%LOCALAPPDATA%\Programs\GeminiTTSStudio` ohne UAC-Elevation).
- **Dateipfade & Windows-Standards**: Das Programm legt keine temporären oder Ausgabedateien im Programmordner ab. Konfiguration liegt in `%APPDATA%\GeminiTTSStudio`, Temp-Audios in `%LOCALAPPDATA%\GeminiTTSStudio\temp`, Ausgabedateien im Standard-Musikordner (`~/Music/Gemini TTS Studio`). Automatische Migration älterer Dateien wird beim Start ausgeführt.

---

## 4. Nächste geplante Erweiterungen (Roadmap)

1. **Multi-Speaker / Skript-Modus**: Parsing von Sprecher-Präfixen wie `[Puck]: Hallo` und `[Aoede]: Hi` mit automatischer Stimmenzuweisung für Dialoge/Hörspiele.
2. **Phonetisches Wörterbuch & Aussprache-Korrektur**: Benutzerdefiniertes Lexikon für Eigennamen, Abkürzungen und Fachbegriffe (z.B. "SQL", "ChatGPT").
3. **Audio-Ducking / Hintergrundmusik**: Sanftes Unterlegen von Ambient-Musik mit automatischer Absenkung bei Sprache und Intro/Outro-Jingles.
4. **Untertitel- & Video-Synchronisation**: Export von zeitgenauen `.srt` und `.vtt`-Untertiteln passend zur generierten Sprache.
5. **Generierungs-Verlauf & A/B-Hörvergleich**: Schnelles Umschalten und Gegenüberstellen von zwei Stimm- oder Tonfall-Varianten.
