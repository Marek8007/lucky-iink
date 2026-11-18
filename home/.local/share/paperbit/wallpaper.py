#!/usr/bin/env python3
"""Centered, synchronized artwork slideshow on the desktop background layer."""
import ctypes as C
import fcntl
import json
import os
import random
from pathlib import Path
import signal
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib
from pixel_rain import PixelRain
from theme_support import image_theme

lock = open(Path(os.environ['XDG_RUNTIME_DIR']) / 'paperbit-wallpaper.lock', 'w')
try:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError:
    raise SystemExit(0)

# openSUSE provides the shared library but not its optional Python typelib.
lib = C.CDLL('libgtk-layer-shell.so.0')
capsule_pointer = C.pythonapi.PyCapsule_GetPointer
capsule_pointer.argtypes = [C.py_object, C.c_char_p]
capsule_pointer.restype = C.c_void_p
def ptr(obj):
    return capsule_pointer(obj.__gpointer__, None)

def bind(name, args):
    fn = getattr(lib, name)
    fn.argtypes = args
    fn.restype = None
    return fn

init = bind('gtk_layer_init_for_window', [C.c_void_p])
layer = bind('gtk_layer_set_layer', [C.c_void_p, C.c_int])
monitor = bind('gtk_layer_set_monitor', [C.c_void_p, C.c_void_p])
anchor = bind('gtk_layer_set_anchor', [C.c_void_p, C.c_int, C.c_int])
zone = bind('gtk_layer_set_exclusive_zone', [C.c_void_p, C.c_int])
keyboard = bind('gtk_layer_set_keyboard_mode', [C.c_void_p, C.c_int])
namespace = bind('gtk_layer_set_namespace', [C.c_void_p, C.c_char_p])

# Only the artwork accepts clicks; the rest of the wallpaper is click-through.
cairo = C.CDLL('libcairo.so.2')
cairo.cairo_region_create.restype = C.c_void_p
class Rectangle(C.Structure):
    _fields_=[('x',C.c_int),('y',C.c_int),('width',C.c_int),('height',C.c_int)]
cairo.cairo_region_create_rectangle.argtypes=[C.POINTER(Rectangle)]
cairo.cairo_region_create_rectangle.restype=C.c_void_p
cairo.cairo_region_destroy.argtypes = [C.c_void_p]
gdk = C.CDLL('libgdk-3.so.0')
gdk.gdk_window_input_shape_combine_region.argtypes = [C.c_void_p, C.c_void_p, C.c_int, C.c_int]
def artwork_input(widget):
    if not widget.get_realized(): return GLib.SOURCE_REMOVE
    square=widget.artwork
    xy=square.translate_coordinates(widget,0,0)
    if xy is not None and square.get_allocated_width()>1:
        rectangle=Rectangle(xy[0],xy[1],square.get_allocated_width(),square.get_allocated_height())
        region=cairo.cairo_region_create_rectangle(C.byref(rectangle))
    else:
        region=cairo.cairo_region_create()
    gdk.gdk_window_input_shape_combine_region(ptr(widget.get_window()), region, 0, 0)
    cairo.cairo_region_destroy(region)
    return GLib.SOURCE_REMOVE

def clicked(widget,event):
    if event.button==1:
        next_image()
        return True
    return False

config_path = Path('/home/marcos/.local/share/paperbit/wallpaper.json')
windows = []
config = {}
current_path = None
current_image = None
queue = []
rotation_timer = None
state_path = Path('/home/marcos/.local/state/paperbit/wallpaper-state.json')
provider = Gtk.CssProvider()
Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

def available_images():
    directory=Path(config.get('image_directory','')).expanduser()
    if not directory.is_dir(): return []
    return sorted(p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in
        ('.png','.jpg','.jpeg','.webp','.bmp','.gif'))

def load_image(path):
    size=max(16,min(1600,int(config['size'])))
    return image_theme(GdkPixbuf.Pixbuf.new_from_file_at_scale(str(path),size,size,True).apply_embedded_orientation())

def render():
    size=max(16,min(1600,int(config['size'])))
    background=config['background'] if current_image else config['placeholder_color']
    provider.load_from_data((
        'window.paperbit-wallpaper { background: '+config['background']+'; }\n'
        '.paperbit-placeholder { background: '+background+'; }'
    ).encode())
    for win,square,image in windows:
        win.rain.configure(config.get('rain',{}))
        square.set_size_request(size,size)
        if current_image: image.set_from_pixbuf(current_image)
        else: image.clear()
        square.show_all()

def next_image():
    global queue,current_path,current_image
    files=available_images()
    queue=[p for p in queue if p in files]
    if config.get('allow_repeats',False):
        # Each selection is independent, including the image currently shown.
        queue=files[:]
        random.shuffle(queue)
    if not queue:
        queue=files[:]
        if config.get('shuffle',True): random.shuffle(queue)
        if len(queue)>1 and queue[0]==current_path: queue[0],queue[1]=queue[1],queue[0]
    while queue:
        path=queue.pop(0)
        try: image=load_image(path)
        except (GLib.Error,OSError) as error:
            print(f'Imagen omitida: {path}: {error}',flush=True)
            continue
        current_path,current_image=path,image
        state_path.parent.mkdir(parents=True,exist_ok=True)
        state_path.write_text(json.dumps({'current':str(path),'remaining':[str(p) for p in queue]},ensure_ascii=False))
        print(f'Ilustración: {path.name} ({image.get_width()}x{image.get_height()})',flush=True)
        break
    render()
    return GLib.SOURCE_CONTINUE

def reload_style():
    global config,current_path,current_image,queue,rotation_timer
    config = json.loads(config_path.read_text())
    if current_path is None:
        try:
            state=json.loads(state_path.read_text())
            current_path=Path(state['current'])
            queue=[Path(p) for p in state.get('remaining',[])]
        except (OSError,ValueError,KeyError): pass
    try: current_image=load_image(current_path) if current_path in available_images() else None
    except (GLib.Error,OSError): current_image=None
    if current_image: render()
    else: next_image()
    if rotation_timer is not None: GLib.source_remove(rotation_timer)
    rotation_timer=GLib.timeout_add_seconds(max(10,int(config.get('rotation_seconds',300))),next_image)
    return GLib.SOURCE_CONTINUE

def add_monitor(display, screen):
    win = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
    win.get_style_context().add_class('paperbit-wallpaper')
    win.set_accept_focus(False)
    init(ptr(win))
    layer(ptr(win), 0)  # Background layer; no reserved screen space.
    monitor(ptr(win), ptr(screen))
    namespace(ptr(win), b'paperbit-wallpaper')
    zone(ptr(win), -1)
    keyboard(ptr(win), 0)
    for edge in range(4):
        anchor(ptr(win), edge, True)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    square = Gtk.EventBox()
    square.get_style_context().add_class('paperbit-placeholder')
    square.set_halign(Gtk.Align.CENTER)
    square.set_valign(Gtk.Align.CENTER)
    square.set_vexpand(True)
    square.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
    square.connect('button-press-event',clicked)
    win.artwork=square
    square.connect('size-allocate',lambda *_: GLib.idle_add(artwork_input,win))
    image = Gtk.Image()
    image.set_halign(Gtk.Align.CENTER)
    image.set_valign(Gtk.Align.CENTER)
    square.add(image)
    # A centered inner widget keeps the square from expanding with its parent.
    frame = Gtk.Box()
    frame.set_halign(Gtk.Align.CENTER)
    frame.set_valign(Gtk.Align.CENTER)
    frame.add(square)
    box.set_center_widget(frame)
    overlay=Gtk.Overlay()
    rain=PixelRain(config.get('rain',{}))
    overlay.add(rain)
    overlay.add_overlay(box)
    win.rain=rain
    win.add(overlay)
    win.connect('realize',lambda *_: GLib.idle_add(artwork_input,win))
    windows.append((win, square, image))
    render()
    win.show_all()

display = Gdk.Display.get_default()
reload_style()
for i in range(display.get_n_monitors()):
    add_monitor(display, display.get_monitor(i))
display.connect('monitor-added', add_monitor)
GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGUSR1, reload_style)
GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGUSR2, next_image)
Gtk.main()
