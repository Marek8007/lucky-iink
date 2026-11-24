#!/usr/bin/env python3
"""Launch GTKLock with Paperbit's native animated background when installed."""
import fcntl
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from theme_support import DARK, tint


def main():
    locker = shutil.which("gtklock")
    root = Path(__file__).parent
    state = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share")
    module = state / "paperbit/gtklock/paperbit-patterns.so"
    if locker and module.is_file():
        try:
            version = subprocess.check_output([locker, "--version"], text=True, timeout=2)
            if re.search(r"\bv?5\.\d+\.", version):
                with tempfile.TemporaryDirectory(prefix="paperbit-gtklock-",
                                                 dir=os.environ.get("XDG_RUNTIME_DIR")) as work:
                    style = Path(work) / "style.css"
                    style.write_text(tint((root / "gtklock.css").read_text(), DARK))
                    config = Path(work) / "config.ini"
                    config.write_text("[main]\n")
                    env = dict(os.environ, PAPERBIT_LOCK_DARK=str(int(DARK)), GDK_BACKEND="wayland")
                    result = subprocess.run([locker, "--config", str(config), "--style", str(style),
                                             "--modules", str(module), "--time-format", "%H:%M",
                                             "--date-format", "[ SESIÓN BLOQUEADA ]"],
                                            env=env)
                    if result.returncode == 0:
                        return 0
        except (OSError, subprocess.SubprocessError) as error:
            print(f"Paperbit: no se pudo iniciar GTKLock ({error}).", flush=True)
    os.execvp("hyprlock", ["hyprlock"])


if __name__ == "__main__":
    runtime = Path(os.environ["XDG_RUNTIME_DIR"])
    display = Path(os.environ.get("WAYLAND_DISPLAY", "wayland")).name
    with (runtime / f"paperbit-gtklock-{display}.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit(0)
        raise SystemExit(main())
