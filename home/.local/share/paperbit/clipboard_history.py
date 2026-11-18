#!/usr/bin/env python3
"""Capture the Wayland clipboard and keep a private, searchable history."""
from contextlib import contextmanager
import fcntl
import hashlib
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

MAX_BYTES = 8 * 1024 * 1024
HISTORY_LIMIT = 50


@contextmanager
def history():
    root = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state")
    directory = root / "paperbit/clipboard"
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = directory / "history.sqlite3"
    os.close(os.open(path, os.O_CREAT | os.O_RDONLY, 0o600))
    connection = sqlite3.connect(path)
    try:
        connection.execute("PRAGMA secure_delete = ON")
        with connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS clips (
                id TEXT PRIMARY KEY,
                mime TEXT NOT NULL,
                data BLOB NOT NULL,
                preview TEXT NOT NULL,
                copied INTEGER NOT NULL,
                favorite INTEGER NOT NULL DEFAULT 0
            )""")
            yield connection
    finally:
        connection.close()


def prune(connection):
    connection.execute("""DELETE FROM clips WHERE favorite = 0 AND id IN (
        SELECT id FROM clips WHERE favorite = 0 ORDER BY copied DESC LIMIT -1 OFFSET ?
    )""", (HISTORY_LIMIT,))


def set_favorite(clip_id, favorite):
    with history() as connection:
        connection.execute("UPDATE clips SET favorite = ? WHERE id = ?", (favorite, clip_id))
        prune(connection)


def remove(clip_id):
    with history() as connection:
        connection.execute("DELETE FROM clips WHERE id = ?", (clip_id,))


def copy(clip_id):
    with history() as connection:
        clip = connection.execute("SELECT mime, data FROM clips WHERE id = ?", (clip_id,)).fetchone()
    if clip is None:
        return False
    mime, data = clip
    result = subprocess.run(["wl-copy", "--type", mime], input=data, timeout=5)
    return result.returncode == 0


def store():
    # wl-paste sets this hint for password managers that advertise sensitive data.
    if os.environ.get("CLIPBOARD_STATE", "data") != "data":
        return
    data = sys.stdin.buffer.read(MAX_BYTES + 1)
    if not data or len(data) > MAX_BYTES:
        return
    mime = subprocess.check_output(
        ["file", "--brief", "--mime-type", "-"], input=data[:65536], timeout=3
    ).decode().strip()
    if mime.startswith("image/"):
        preview = f"Imagen · {mime.split('/', 1)[1].upper()} · {max(1, round(len(data) / 1024))} KB"
    else:
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            return
        if "\0" in text or not text.strip():
            return
        mime = "text/plain;charset=utf-8"
        preview = " ".join(text[:500].split())[:180] or "Texto"
    clip_id = hashlib.sha256(data).hexdigest()
    with history() as connection:
        connection.execute("""INSERT INTO clips (id, mime, data, preview, copied)
            VALUES (?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET copied = excluded.copied
            """, (clip_id, mime, data, preview, time.time_ns()))
        prune(connection)


def watch():
    runtime = Path(os.environ["XDG_RUNTIME_DIR"])
    socket = Path(os.environ["WAYLAND_DISPLAY"]).name
    with (runtime / f"paperbit-clipboard-{socket}.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        os.set_inheritable(lock.fileno(), True)
        os.execvp("wl-paste", [
            "wl-paste", "--no-newline", "--watch", sys.executable, str(Path(__file__)), "store"
        ])


if __name__ == "__main__":
    if sys.argv[1:] == ["watch"]:
        watch()
    elif sys.argv[1:] == ["store"]:
        store()
    else:
        raise SystemExit("Uso: clipboard_history.py watch|store")
