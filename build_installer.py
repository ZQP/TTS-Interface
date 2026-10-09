"""
Build script to compile both the Windows Executable and the Non-Admin Inno Setup Installer.
Generates:
1. dist/GeminiTTSStudio.exe (Standalone Portable EXE)
2. dist/installer/GeminiTTSStudio-Setup-3.0.0.exe (Non-Admin Windows Setup Installer)
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DIST_DIR = BASE_DIR / "dist"
INSTALLER_DIR = DIST_DIR / "installer"
ISS_FILE = BASE_DIR / "installer.iss"


def find_iscc() -> Path | None:
    """Locate the Inno Setup Command-Line Compiler (ISCC.exe)."""
    # 1. Check in PATH
    in_path = shutil.which("iscc")
    if in_path:
        return Path(in_path)

    # 2. Check standard installation directories
    candidate_paths = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Inno Setup 6" / "ISCC.exe",
        Path("C:/Program Files (x86)/Inno Setup 6/ISCC.exe"),
        Path("C:/Program Files/Inno Setup 6/ISCC.exe"),
        Path(os.environ.get("ProgramFiles", "")) / "Inno Setup 6" / "ISCC.exe",
        Path(os.environ.get("ProgramFiles(x86)", "")) / "Inno Setup 6" / "ISCC.exe",
    ]

    for p in candidate_paths:
        if p.exists():
            return p

    return None


def build_installer():
    print("=" * 60)
    print("=== Building Gemini TTS Studio - Windows Installer ===")
    print("=" * 60)

    # 1. Check / Build standalone EXE
    target_exe = DIST_DIR / "GeminiTTSStudio.exe"
    force_rebuild = "--rebuild" in sys.argv
    needs_rebuild = force_rebuild or not target_exe.exists()

    if not needs_rebuild and target_exe.exists():
        exe_mtime = target_exe.stat().st_mtime
        # Check if any python or asset file was modified after the EXE was built
        source_files = list(BASE_DIR.glob("*.py")) + list((BASE_DIR / "src").glob("*.py")) + list((BASE_DIR / "assets").glob("*"))
        if any(f.stat().st_mtime > exe_mtime for f in source_files):
            print("\n[*] Quellcodedateien oder Assets wurden geaendert. EXE wird neu gebaut...")
            needs_rebuild = True

    if needs_rebuild:
        print("\n[1/2] Erstelle aktuelle Standalone EXE mit PyInstaller...")
        import build_exe
        success = build_exe.build_executable()
        if not success or not target_exe.exists():
            print("[!] Fehler: Standalone EXE konnte nicht erstellt werden.")
            return False
    else:
        print(f"\n[1/2] Standalone EXE ist aktuell: {target_exe.name} ({target_exe.stat().st_size / (1024*1024):.1f} MB)")

    # 2. Locate Inno Setup Compiler
    iscc_path = find_iscc()
    if not iscc_path:
        print("\n[!] Inno Setup Compiler (ISCC.exe) wurde nicht gefunden.")
        print("    Bitte installiere Inno Setup 6 mit folgendem Befehl:")
        print("    winget install JRSoftware.InnoSetup")
        return False

    print(f"\n[2/2] Inno Setup Compiler gefunden: {iscc_path}")
    INSTALLER_DIR.mkdir(parents=True, exist_ok=True)

    cmd = [str(iscc_path), str(ISS_FILE)]
    print(f"Kompiliere Installer mit: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, cwd=str(BASE_DIR))
    if result.returncode == 0:
        # Find generated setup file
        setup_files = list(INSTALLER_DIR.glob("GeminiTTSStudio-Setup-*.exe"))
        if setup_files:
            latest_setup = max(setup_files, key=lambda f: f.stat().st_mtime)
            print("\n" + "=" * 60)
            print("[+] INSTALLER ERFOLGREICH ERSTELLT!")
            print(f"Pfad:       {latest_setup.resolve()}")
            print(f"Dateigröße: {latest_setup.stat().st_size / (1024*1024):.1f} MB")
            print("=" * 60)
            return True

    print("\n[-] Kompilierung des Installers fehlgeschlagen!")
    return False


if __name__ == "__main__":
    success = build_installer()
    sys.exit(0 if success else 1)
