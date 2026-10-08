"""
Gemini TTS Interface - Main Entry Point
"""

import sys
import os

# Ensure the root directory is on the python search path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.gui import GeminiTTSApp


def main():
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("makammi.geminittsstudio.desktop.2.3")
        except Exception:
            pass

    app = GeminiTTSApp()
    app.mainloop()


if __name__ == "__main__":
    main()
