"""
Audio converter module using FFmpeg
"""

import subprocess
import shutil
import os
import sys
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import imageio_ffmpeg
    IMAGEIO_FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    IMAGEIO_FFMPEG_EXE = None


def get_ffmpeg_path() -> str:
    """Find FFmpeg binary (imageio-ffmpeg bundle or system PATH)."""
    if IMAGEIO_FFMPEG_EXE and os.path.exists(IMAGEIO_FFMPEG_EXE):
        return IMAGEIO_FFMPEG_EXE
    
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    
    raise RuntimeError(
        "FFmpeg wurde nicht gefunden. Bitte installiere FFmpeg oder imageio-ffmpeg."
    )


def convert_audio(
    input_file: Path | str,
    output_file: Path | str,
    codec: str = "aac",
    channels: int = 1,
    sample_rate: int = 44100,
    bitrate: Optional[str] = "64k",
    faststart: bool = True,
) -> Path:
    """
    Convert an audio file to target format with specified encoding parameters.
    
    Default parameters adhere to web-streaming standard:
    - Codec: AAC (AAC-LC)
    - Channels: 1 (Mono)
    - Sample rate: 44100 Hz
    - Bitrate: 64 kbit/s
    - Container: MP4/M4A with +faststart
    """
    ffmpeg_exe = get_ffmpeg_path()
    input_path = Path(input_file).resolve()
    output_path = Path(output_file).resolve()
    
    if not input_path.exists():
        raise FileNotFoundError(f"Eingabedatei nicht gefunden: {input_path}")
    
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as dir_err:
        print(f"Hinweis: Ausgabeordner konnte nicht erstellt werden: {dir_err}")
    
    # Build FFmpeg command arguments with forward-slash POSIX paths for rock-solid Windows compatibility
    cmd = [
        ffmpeg_exe,
        "-y",               # Overwrite output
        "-i", input_path.as_posix(),
        "-c:a", codec,
        "-ac", str(channels),
        "-ar", str(sample_rate),
    ]
    
    # Add bitrate if applicable
    if bitrate and codec != "pcm_s16le":
        cmd.extend(["-b:a", str(bitrate)])
    
    # Add FastStart flag for MP4/M4A containers
    ext = output_path.suffix.lower()
    if faststart and ext in [".mp4", ".m4a", ".mov"]:
        cmd.extend(["-movflags", "+faststart"])
    
    # Add output file destination
    cmd.append(output_path.as_posix())

    # Configure headless process creation (suppresses console/cmd window popups on Windows)
    startupinfo = None
    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NO_WINDOW
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    # Run FFmpeg conversion
    process = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        startupinfo=startupinfo,
        creationflags=creationflags
    )
    
    if process.returncode != 0:
        err_lower = (process.stderr or "").lower()
        # If output destination failed (e.g. missing folder, OneDrive virtualization, locked path), retry to safe local fallback directory
        if any(k in err_lower for k in ["no such file or directory", "error opening output", "permission denied", "cannot open"]):
            try:
                fallback_dir = Path(tempfile.gettempdir()) / "GeminiTTSStudio_Output"
                fallback_dir.mkdir(parents=True, exist_ok=True)
                fallback_file = fallback_dir / output_path.name
                fallback_cmd = list(cmd[:-1]) + [fallback_file.as_posix()]
                fb_proc = subprocess.run(
                    fallback_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    startupinfo=startupinfo,
                    creationflags=creationflags
                )
                if fb_proc.returncode == 0 and fallback_file.exists() and fallback_file.stat().st_size > 0:
                    try:
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(fallback_file, output_path)
                        return output_path
                    except Exception:
                        return fallback_file
            except Exception as fb_err:
                print(f"Fallback-Konvertierung fehlgeschlagen: {fb_err}")

        # Extract only the relevant error message lines instead of dumping 30 lines of FFmpeg compiler banners
        raw_lines = [l.strip() for l in (process.stderr or "").splitlines() if l.strip()]
        error_lines = [l for l in raw_lines if any(k in l.lower() for k in ["error", "invalid", "cannot", "failed"])]
        summary = "\n".join(error_lines[-3:]) if error_lines else (raw_lines[-1] if raw_lines else "Unbekannter Fehler")
        raise RuntimeError(f"FFmpeg Fehler beim Konvertieren: {summary}")
    
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError(f"Ausgabedatei wurde nicht erfolgreich erstellt: {output_path}")
    
    return output_path


def get_command_preview(
    input_file: str = "eingabe.wav",
    output_file: str = "ausgabe.mp4",
    codec: str = "aac",
    channels: int = 1,
    sample_rate: int = 44100,
    bitrate: Optional[str] = "64k",
    faststart: bool = True
) -> str:
    """Generate the human-readable FFmpeg command string for display."""
    ext = Path(output_file).suffix.lower()
    flags = f"-c:a {codec}"
    if bitrate and codec != "pcm_s16le":
        flags += f" -b:a {bitrate}"
    flags += f" -ac {channels} -ar {sample_rate}"
    if faststart and ext in [".mp4", ".m4a"]:
        flags += " -movflags +faststart"
    return f"ffmpeg -i {input_file} {flags} {output_file}"
