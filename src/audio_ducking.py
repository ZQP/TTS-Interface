"""
Audio Ducking & Background Music Engine for Gemini TTS Studio
Blends ambient music and background tracks with synthesized speech using
FFmpeg sidechain compression and automated volume ducking.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional

from .audio_converter import get_ffmpeg_path


def apply_audio_ducking(
    speech_file: Path,
    bgm_file: Path,
    output_file: Path,
    bgm_normal_volume: float = 0.40,
    ducked_volume_factor: float = 0.15,
    attack_ms: int = 350,
    release_ms: int = 1200,
    bitrate: str = "64k",
    codec: str = "aac",
    faststart: bool = True
) -> Path:
    """
    Mixes speech and background music together with sidechain ducking.
    Whenever speech is active, the music volume drops smoothly; during pauses,
    the music gracefully returns to normal ambient volume.
    """
    ffmpeg_exe = get_ffmpeg_path()
    speech_file = Path(speech_file).resolve()
    bgm_file = Path(bgm_file).resolve()
    output_file = Path(output_file).resolve()
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if not speech_file.exists():
        raise FileNotFoundError(f"Sprachdatei nicht gefunden: {speech_file}")
    if not bgm_file.exists():
        raise FileNotFoundError(f"Hintergrundmusik-Datei nicht gefunden: {bgm_file}")

    # Clamp volumes
    bgm_normal_volume = max(0.05, min(1.0, bgm_normal_volume))
    ducked_volume_factor = max(0.01, min(1.0, ducked_volume_factor))

    # Calculate compression ratio from ducked factor (e.g. 0.15 volume -> ratio ~ 7:1)
    ratio = max(2.0, min(20.0, 1.0 / ducked_volume_factor))
    attack = max(10, min(2000, attack_ms))
    release = max(100, min(5000, release_ms))

    # Complex filter:
    # 1. Base volume for music
    # 2. Sidechain compression triggered by speech [0:a] onto music [1:a]
    # 3. Mix both streams together, ending when the speech track ends
    filter_complex = (
        f"[1:a]volume={bgm_normal_volume:.2f}[bgm_base];"
        f"[bgm_base][0:a]sidechaincompress=threshold=0.08:ratio={ratio:.1f}:attack={attack}:release={release}[ducked_bgm];"
        f"[0:a][ducked_bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
    )

    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", str(speech_file),
        "-stream_loop", "-1",
        "-i", str(bgm_file),
        "-filter_complex", filter_complex,
        "-map", "[aout]",
        "-c:a", codec,
        "-b:a", bitrate,
        "-ac", "1",
        "-ar", "44100",
    ]

    if faststart and output_file.suffix.lower() in [".mp4", ".m4a"]:
        cmd.extend(["-movflags", "+faststart"])

    cmd.append(str(output_file))

    # Run FFmpeg headless
    startupinfo = None
    creationflags = 0
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        creationflags = subprocess.CREATE_NO_WINDOW

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        startupinfo=startupinfo,
        creationflags=creationflags
    )

    if result.returncode != 0:
        # Fallback to simpler volume mix if sidechaincompress fails on minimal builds
        print(f"Hinweis: Sidechain fehlgeschlagen, versuche linearen Mix ({result.stderr.decode('utf-8', errors='ignore')[:150]})")
        fallback_filter = f"[1:a]volume={bgm_normal_volume * 0.3:.2f}[bgm_soft];[0:a][bgm_soft]amix=inputs=2:duration=first[aout]"
        cmd_fallback = [
            ffmpeg_exe, "-y",
            "-i", str(speech_file),
            "-stream_loop", "-1",
            "-i", str(bgm_file),
            "-filter_complex", fallback_filter,
            "-map", "[aout]",
            "-c:a", codec,
            "-b:a", bitrate,
            "-ac", "1",
            str(output_file)
        ]
        res_fb = subprocess.run(
            cmd_fallback,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            startupinfo=startupinfo,
            creationflags=creationflags
        )
        if res_fb.returncode != 0:
            raise RuntimeError(f"FFmpeg Ducking fehlgeschlagen: {res_fb.stderr.decode('utf-8', errors='ignore')}")

    return output_file
