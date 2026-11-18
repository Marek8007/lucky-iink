#!/usr/bin/env python3
"""Open the Paperbit clipboard menu below Waybar on the clicked monitor."""
import ctypes
import fcntl
import json
import os
from pathlib import Path
import subprocess

import gi
gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, Gtk, Pango

import clipboard_history
from theme_support import tint_bytes

WIDTH = 400
CSS = b"""
window.clipboard-overlay { background: transparent; }
.clipboard-card { background: #ffffff; color: #171717; border: 2px solid #171717; }
.clipboard-card label, .clipboard-card entry {
    font-family: "JetBrainsMono Nerd Font", monospace; font-size: 12px; color: #171717;
}
.clipboard-card .clipboard-title {
    font-family: "Classic Console"; font-size: 18px; background: #efc7d1; padding: 8px;
    border-bottom: 1px solid #171717;
}
.clipboard-card list, .clipboard-card entry, .clipboard-card button {
    background: #ffffff; background-image: none; color: #171717; border-radius: 0;
}
.clipboard-card button:hover, .clipboard-card button:checked,
.clipboard-card row:hover, .clipboard-card row:selected { background: #efc7d1; }
.clipboard-card row { padding: 4px 6px; border-bottom: 1px solid #b8b8b8; }
.clipboard-card .favorite label { color: #884258; }
"""


def create_overlay():
    def query(command):
        return json.loads(subprocess.check_output(["hyprctl", "-j", command], timeout=3))

    cursor = query("cursorpos")
    screens = query("monitors")
    screen = next(m for m in screens if m["focused"])
    for candidate in screens:
        if (0 <= cursor["x"] - candidate["x"] < candidate["width"] / candidate["scale"]
                and 0 <= cursor["y"] - candidate["y"] < candidate["height"] / candidate["scale"]):
            screen = candidate
            break

    display = Gdk.Display.get_default()
    monitors = [display.get_monitor(i) for i in range(display.get_n_monitors())]
    monitor = next((m for m in monitors if (m.get_geometry().x, m.get_geometry().y)
                    == (screen["x"], screen["y"])), monitors[0])
    bars = query("layers").get(screen["name"], {}).get("levels", {})
    below = max((item["y"] + item["h"] - screen["y"] for level in bars.values()
                 for item in level if item["namespace"] == "waybar"), default=42)
    width = monitor.get_geometry().width
    x = max(8, min(round(cursor["x"] - screen["x"] - WIDTH / 2), width - WIDTH - 8))

    library = ctypes.CDLL("libgtk-layer-shell.so.0")
    pointer = ctypes.pythonapi.PyCapsule_GetPointer
    pointer.argtypes = [ctypes.py_object, ctypes.c_char_p]
    pointer.restype = ctypes.c_void_p

    def call(name, types, *args):
        function = getattr(library, "gtk_layer_" + name)
        function.argtypes = [ctypes.c_void_p, *types]
        function.restype = None
        function(pointer(window.__gpointer__, None), *args)

    window = Gtk.Window()
    window.set_app_paintable(True)
    window.set_visual(window.get_screen().get_rgba_visual())
    window.get_style_context().add_class("clipboard-overlay")
    call("init_for_window", [])
    call("set_layer", [ctypes.c_int], 3)
    call("set_monitor", [ctypes.c_void_p], pointer(monitor.__gpointer__, None))
    call("set_namespace", [ctypes.c_char_p], b"paperbit-clipboard")
    call("set_exclusive_zone", [ctypes.c_int], -1)
    call("set_keyboard_mode", [ctypes.c_int], 1)
    for edge in range(4):
        call("set_anchor", [ctypes.c_int, ctypes.c_int], edge, True)
    y = below + 2
    list_height_limit = max(48, min(315, monitor.get_geometry().height - y - 120))
    return window, x, y, list_height_limit


class ClipboardMenu:
    def __init__(self):
        self.window, x, y, self.list_height_limit = create_overlay()
        style = Gtk.CssProvider()
        style.load_from_data(tint_bytes(CSS))
        Gtk.StyleContext.add_provider_for_screen(
            self.window.get_screen(), style, Gtk.STYLE_PROVIDER_PRIORITY_USER + 50
        )

        self.card = Gtk.EventBox()
        self.card.get_style_context().add_class("clipboard-card")
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        content.set_size_request(WIDTH - 4, -1)
        self.card.add(content)
        self.title = Gtk.Label(xalign=0)
        self.title.get_style_context().add_class("clipboard-title")
        content.pack_start(self.title, False, False, 0)

        filters = Gtk.Box(spacing=6, margin_start=8, margin_end=8)
        self.search = Gtk.SearchEntry(placeholder_text="Buscar…", hexpand=True)
        self.favorites = Gtk.ToggleButton(label="★ Favoritos")
        filters.add(self.search)
        filters.add(self.favorites)
        content.pack_start(filters, False, False, 0)

        self.rows = Gtk.ListBox(activate_on_single_click=True)
        self.message = Gtk.Label(margin_top=16, margin_bottom=16)
        self.rows.set_placeholder(self.message)
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroll.add(self.rows)
        content.pack_start(self.scroll, True, True, 0)

        self.status = Gtk.Label(label="Pulsa una entrada para copiarla", margin_bottom=8)
        content.pack_start(self.status, False, False, 0)
        fixed = Gtk.Fixed()
        fixed.put(self.card, x, y)
        backdrop = Gtk.EventBox()
        backdrop.add(fixed)
        self.window.add(backdrop)

        backdrop.connect("button-press-event", self.on_outside)
        self.window.connect("key-press-event", self.on_key)
        self.window.connect("destroy", lambda *_: Gtk.main_quit())
        self.rows.connect("row-activated", self.copy_row)
        self.search.connect("search-changed", self.refresh)
        self.search.connect("activate", self.copy_first)
        self.favorites.connect("toggled", self.refresh)

    def on_outside(self, _widget, event):
        target = Gtk.get_event_widget(event)
        if target is self.card or (target is not None and target.is_ancestor(self.card)):
            return False
        self.window.destroy()
        return True

    def on_key(self, _widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.window.destroy()
            return True
        return False

    def copy_first(self, _entry):
        row = self.rows.get_row_at_index(0)
        if row is not None:
            self.copy_row(self.rows, row)

    def copy_row(self, _box, row):
        try:
            if clipboard_history.copy(row.clip_id):
                self.window.destroy()
                return
        except (OSError, subprocess.TimeoutExpired):
            pass
        self.status.set_text("No se pudo copiar la entrada")

    def favorite(self, _button, clip_id, current):
        clipboard_history.set_favorite(clip_id, not current)
        self.refresh()

    def remove(self, _button, clip_id):
        clipboard_history.remove(clip_id)
        self.refresh()

    def refresh(self, *_):
        only_favorites = self.favorites.get_active()
        self.title.set_text("PORTAPAPELES / FAVORITOS" if only_favorites else "PORTAPAPELES / HISTORIAL")
        search = self.search.get_text().strip().casefold()
        for row in self.rows.get_children():
            row.destroy()
        self.message.set_text("Sin resultados" if search else
                              "Todavía no hay favoritos" if only_favorites else
                              "Todavía no hay nada copiado")
        self.message.show()

        with clipboard_history.history() as connection:
            rows = connection.execute("""SELECT id, preview, favorite FROM clips
                WHERE favorite >= ? ORDER BY copied DESC""", (int(only_favorites),)).fetchall()
        for clip_id, preview, favorite in rows:
            if search not in preview.casefold():
                continue
            row = Gtk.ListBoxRow()
            row.clip_id = clip_id
            line = Gtk.Box(spacing=6)
            label = Gtk.Label(label=preview, xalign=0, ellipsize=Pango.EllipsizeMode.END)
            line.pack_start(label, True, True, 0)
            star = Gtk.Button(label="★" if favorite else "☆")
            if favorite:
                star.get_style_context().add_class("favorite")
            star.set_tooltip_text("Quitar de favoritos" if favorite else "Añadir a favoritos")
            star.connect("clicked", self.favorite, clip_id, favorite)
            line.pack_start(star, False, False, 0)
            delete = Gtk.Button(label="×", tooltip_text="Eliminar entrada")
            delete.connect("clicked", self.remove, clip_id)
            line.pack_start(delete, False, False, 0)
            row.add(line)
            self.rows.add(row)
            row.show_all()

        # Gtk.Fixed allocates the minimum size, so request room for the visible rows.
        self.rows.show()
        _, natural_height = self.rows.get_preferred_height()
        self.scroll.set_min_content_height(min(natural_height, self.list_height_limit))
        self.scroll.get_vadjustment().set_value(0)

    def run(self):
        self.refresh()
        self.window.show_all()
        self.search.grab_focus()
        Gtk.main()


if __name__ == "__main__":
    runtime = Path(os.environ["XDG_RUNTIME_DIR"])
    with (runtime / "paperbit-clipboard-popup.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit(0)
        ClipboardMenu().run()
