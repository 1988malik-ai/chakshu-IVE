"""Native folder picker for local Chakshu workstation (returns absolute paths)."""

from __future__ import annotations

import platform
import subprocess
from pathlib import Path


def pick_folder(initial_dir: str | None = None) -> str | None:
    """
    Open OS folder chooser. Works when API runs on the examiner's machine.
    Returns absolute path or None if cancelled / unavailable.
    """
    initial = Path(initial_dir).expanduser() if initial_dir else Path.home()
    if not initial.is_dir():
        initial = initial.parent if initial.parent.is_dir() else Path.home()

    system = platform.system()
    if system == "Darwin":
        prompt = "Select secure media folder"
        if initial.is_dir():
            script = (
                f'POSIX path of (choose folder with prompt "{prompt}" '
                f'default location POSIX file "{initial}")'
            )
        else:
            script = f'POSIX path of (choose folder with prompt "{prompt}")'
        try:
            r = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=600,
            )
            if r.returncode == 0:
                chosen = r.stdout.strip()
                if chosen:
                    return str(Path(chosen).resolve())
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass

    if system == "Windows":
        try:
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            chosen = filedialog.askdirectory(
                parent=root,
                initialdir=str(initial),
                title="Select secure media folder",
                mustexist=True,
            )
            root.destroy()
            if chosen:
                return str(Path(chosen).resolve())
        except Exception:
            pass

    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        chosen = filedialog.askdirectory(
            parent=root,
            initialdir=str(initial),
            title="Select secure media folder",
            mustexist=True,
        )
        root.destroy()
        if chosen:
            return str(Path(chosen).resolve())
    except Exception:
        pass

    return None
