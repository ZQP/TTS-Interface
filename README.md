# Gemini TTS Studio (Windows)

Ein modernes, professionelles Windows Desktop-Interface zur Text-in-Sprache-Umwandlung (Text-to-Speech) basierend auf der **Google Gemini API**. 

Unterstützt native **Audio-Tags / Regieanweisungen** (z. B. `[lachen]`, `[flüstern]`, `[traurig]`, `[begeistert]`, `[Pause]`), eine reiche Stimmenauswahl, automatische Spracherkennung, **Smart Chunking für lange Texte** und eine präzise AAC/MP4/M4A-Audiokonvertierung via FFmpeg inkl. Fast-Start-Flag für Web-Streaming.

---

## 📑 Inhaltsverzeichnis

- [Features](#features)
- [Schnellstart](#schnellstart)
- [Standalone EXE erstellen](#standalone-exe-erstellen)
- [Architektur & Entwickler-Dokumentation](#architektur--entwickler-dokumentation)
- [FFmpeg Konvertierungs-Profil](#ffmpeg-konvertierungs-profil)
- [Lizenz](#lizenz)

---

## Features (v3.0.0)

- 🎙️ **Gemini 3.8 TTS Engine**: Volle Unterstützung für `gemini-3.8-flash-tts` (Studio-Qualität & Flaggschiff) und `gemini-3.8-flash-lite-tts` (High-Speed & Massenverarbeitung).
- 🎭 **Multi-Sprecher & Dialog-Skript (Neu in v3.0.0)**: Vollwertiger Hörspiel- & Skriptmodus mit automatischer Sprechererkennung (`[Erzähler]: ... [Anna]: ... [Ben]: ...`), individueller Stimmenzuweisung pro Rolle, konfigurierbaren Sprechpausen und nahtloser Sequenz-Synthese.
- 📖 **Phonetisches Wörterbuch & Aussprache-Lexikon (Neu in v3.0.0)**: Benutzerdefinierte Ausspracheregeln (`custom_lexicon.json`), Akronym-Übersetzung (z. B. `SQL` → `Es-Kju-Ell`), Regex-Muster und sofortige Audio-Probehörfunktion.
- 🎵 **Sidechain Audio-Ducking & Hintergrundmusik (Neu in v3.0.0)**: Nahtloses Einmischen von Hintergrundmusik (`.mp3`, `.wav`) mit automatischer Lautstärkeabsenkung während des Sprechens (-14 dB Ducking) und sanftem Fade-Out am Sprach-Ende.
- 📝 **Frame-genaues Untertitel-Studio (Neu in v3.0.0)**: Dedizierte Subtitle-Suite mit 16:9 Cinema-Monitor, Live-Overlay, CPS-Lesbarkeitsprüfung (optimal / gut / zu schnell), Inline-Cue-Editor und 1-Klick-Export nach `.SRT` und `.VTT`.
- ⚖️ **Take-Historie & A/B-Vergleichs-Labor (Neu in v3.0.0)**: Automatische Erfassung aller Takes der Sitzung mit Slot-Zuweisung (Slot A & Slot B) und 1-Klick-Umschaltung für sofortigen Hörvergleich.
- 🎭 **Expressive Regie-Cues & Audio-Tags**: 1-Klick-Toolbar für native Emotionen und non-verbale Geräusche: `<laughs>` (Lachen), `<sigh>` (Seufzen), `<gasp>` (Einatmen), `<throat-clearing>` (Räuspern), `|mhm|` (Zustimmung), `[whispering]` (Flüstern) und `[pause]`.
- 👥 **Große Stimmenbibliothek (50+ Stimmen)**: Neben den beliebten Allroundern (*Erinome, Puck, Charon, Kore, Fenrir*) stehen native deutsche Rollen-Personas bereit (*Anwältin, Arzt, Wissenschaftler, Professorin, Lehrer, Moderatorin, Erzählerin, Kundenservice*).
- 🔄 **Integrierter Auto-Updater**: Erkennt neue Releases auf GitHub automatisch beim Start und aktualisiert die App per 1-Klick nahtlos im laufenden Betrieb.
- 📜 **Smart Chunking (Keine Timeouts bei langen Texten)**: Zerlegt lange Texte intelligent an Satz- und Absatzgrenzen und fügt die Audiodaten nahtlos zusammen.
- 🌐 **Sprachauswahl & Automatische Übersetzung**: 32 Weltsprachen mit automatischer Spracherkennung oder 1-Klick-Übersetzung.
- 🎛️ **Optimierte Audio-Formate**:
  - Standard-Preset: **AAC-LC**, **Mono**, **64 kbit/s**, **44.100 Hz / 48.000 Hz**, Container: **MP4 / M4A** mit `+faststart` Streaming-Flag.
  - Weitere Formate: MP3 (192k/320k), verlustfreies WAV & FLAC sowie freier Modus („Benutzerdefiniert“).
- 🔊 **Integrierter Audio-Player mit Waveform & Scrubbing**: Flüssiges Spulen mit der Maus, Pause, Lautstärkeregelung.
- 💾 **Export & Batch-Verarbeitung**: Konvertierung und Export einzelner Texte oder ganzer Dokumenten-Warteschlangen.
- 📦 **Standalone Portable EXE**: Kann ohne Python-Installation direkt auf jedem Windows-Rechner ausgeführt werden.

---

## Schnellstart

### 1. Repository klonen
```bash
git clone https://github.com/MaKammi/TTS-Interface.git
cd TTS-Interface
```

### 2. Abhängigkeiten installieren
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. API-Key einrichten
Erstelle eine `.env`-Datei im Hauptverzeichnis (oder kopiere `.env.example`):
```env
GEMINI_API_KEY=dein_gemini_api_key
```
*(Alternativ kann der API-Key direkt in der App über den Button `🔑 API-Key` eingegeben werden.)*

### 4. Anwendung starten
```bash
python main.py
```

---

## Standalone EXE & Windows Setup-Installer erstellen

### 1. Standalone Portable EXE erstellen
Erstellt eine eigenständige `.exe` unter `dist/GeminiTTSStudio.exe`:
```bash
python build_exe.py
```
*(Oder per Doppelklick auf `build.bat` ausführen.)*

### 2. Windows Installationsprogramm (Inno Setup) erstellen
Erstellt einen vollwertigen Windows-Installer (`dist/installer/GeminiTTSStudio-Setup-2.4.4.exe`), der **ohne Administratorrechte** im Benutzerprofil installiert werden kann:
```bash
python build_installer.py
```
*(Oder per Doppelklick auf `build_installer.bat` ausführen.)*

- **Ohne Adminrechte**: Installiert nahtlos in `%LOCALAPPDATA%\Programs\GeminiTTSStudio` (wie VS Code User Installer).
- **Keine Dateiverunreinigung**: Konfigurationen liegen in `%APPDATA%\GeminiTTSStudio`, Temp-Audios in `%LOCALAPPDATA%\GeminiTTSStudio\temp`, Ausgabedateien im Musik-Ordner (`~/Music/Gemini TTS Studio`).
- **Verknüpfungen**: Startmenü- und Desktop-Icons mit individuellem App-Icon.
- **GitHub Actions**: Automatische Builds und Release-Bereitstellung über `.github/workflows/build-and-release.yml`.

---

## Architektur & Entwickler-Dokumentation

Für Entwickler und KI-Assistenten stehen im Verzeichnis [`docs/`](docs/) ausführliche Dokumente bereit:
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**: Vollständige Systemarchitektur, Datenfluss-Diagramme, Modul-Spezifikationen und FFmpeg-Pipeline.
- **[docs/AI_HANDOVER.md](docs/AI_HANDOVER.md)**: Handover-Leitfaden für nachfolgende KI-Agenten, API-Besonderheiten, Lessons Learned und Roadmap.

---

## FFmpeg Konvertierungs-Profil

Das integrierte Web-Optimierungs-Preset nutzt folgenden FFmpeg-Befehl:
```bash
ffmpeg -i eingabe.wav -c:a aac -b:a 64k -ac 1 -ar 44100 -movflags +faststart ausgabe.mp4
```

---

## Lizenz
Privates Repository für MaKammi.
