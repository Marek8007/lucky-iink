#!/usr/bin/env python3
"""Calendar dropdown below the clicked clock, using a temporary overlay layer."""
import ctypes as C
import datetime
import fcntl
import json
import locale
import os
from pathlib import Path
import signal
import subprocess
import gi

try:
    locale.setlocale(locale.LC_ALL,'es_ES.UTF-8')
    # Gtk initializes locale from the environment; Spanish weeks start Monday.
    os.environ['LC_ALL']='es_ES.UTF-8'
except locale.Error:pass
gi.require_version('Gtk','3.0')
from gi.repository import Gtk,Gdk,GLib
from calendar_grid import MonthGrid
from theme_support import tint_bytes

runtime=Path(os.environ['XDG_RUNTIME_DIR'])
lock=open(runtime/'paperbit-calendar.lock','a+')
try:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
except BlockingIOError:
    lock.seek(0)
    try:os.kill(int(lock.read().strip()),signal.SIGUSR1)
    except (ValueError,ProcessLookupError):pass
    raise SystemExit(0)
lock.seek(0);lock.truncate();lock.write(str(os.getpid()));lock.flush()

instances=json.loads(subprocess.check_output(['hyprctl','-j','instances']))
instance=os.environ.get('HYPRLAND_INSTANCE_SIGNATURE') or instances[0]['instance']
base=['hyprctl','-i',instance]
cursor=json.loads(subprocess.check_output(base+['-j','cursorpos']))
monitors=json.loads(subprocess.check_output(base+['-j','monitors']))
screen=next((m for m in monitors if m['x']<=cursor['x']<m['x']+m['width']/m['scale']
    and m['y']<=cursor['y']<m['y']+m['height']/m['scale']),next(m for m in monitors if m['focused']))
layers=json.loads(subprocess.check_output(base+['-j','layers']))
bars=[l for level in layers[screen['name']]['levels'].values() for l in level if l['namespace']=='waybar']
below=max((b['y']+b['h']-screen['y'] for b in bars),default=42)
width=320
x=max(12,min(round(cursor['x']-screen['x']-width/2),round(screen['width']/screen['scale'])-width-12))
y=below+2

lib=C.CDLL('libgtk-layer-shell.so.0')
capsule=C.pythonapi.PyCapsule_GetPointer
capsule.argtypes=[C.py_object,C.c_char_p];capsule.restype=C.c_void_p
def ptr(obj):return capsule(obj.__gpointer__,None)
def api(name,args):
    f=getattr(lib,'gtk_layer_'+name);f.argtypes=args;f.restype=None;return f
init=api('init_for_window',[C.c_void_p])
layer=api('set_layer',[C.c_void_p,C.c_int])
monitor=api('set_monitor',[C.c_void_p,C.c_void_p])
anchor=api('set_anchor',[C.c_void_p,C.c_int,C.c_int])
zone=api('set_exclusive_zone',[C.c_void_p,C.c_int])
keyboard=api('set_keyboard_mode',[C.c_void_p,C.c_int])
namespace=api('set_namespace',[C.c_void_p,C.c_char_p])

display=Gdk.Display.get_default()
gdk_monitor=None
for i in range(display.get_n_monitors()):
    candidate=display.get_monitor(i)
    geometry=candidate.get_geometry()
    if abs(geometry.x-screen['x'])<=1 and abs(geometry.y-screen['y'])<=1:
        gdk_monitor=candidate;break
if gdk_monitor is None:gdk_monitor=display.get_primary_monitor() or display.get_monitor(0)

window=Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
window.get_style_context().add_class('paperbit-calendar-overlay')
window.set_app_paintable(True)
window.set_visual(window.get_screen().get_rgba_visual())
init(ptr(window));layer(ptr(window),3);monitor(ptr(window),ptr(gdk_monitor))
namespace(ptr(window),b'paperbit-calendar')
zone(ptr(window),-1);keyboard(ptr(window),1)
for edge in range(4):anchor(ptr(window),edge,True)

css=Gtk.CssProvider()
css.load_from_data(tint_bytes(b'''
window.paperbit-calendar-overlay { background: transparent; border: none; }
.paperbit-calendar-backdrop { background: transparent; }
.paperbit-calendar-card { background: #ffffff; color: #171717; border: 2px solid #171717;
    border-radius: 0; box-shadow: 3px 3px 0 #efc7d1; }
.paperbit-calendar-card label, .paperbit-calendar-card button, .paperbit-calendar-card calendar {
    font-family: "JetBrainsMono Nerd Font", monospace; font-size: 12px; color: #171717; }
.paperbit-calendar-card .calendar-heading { font-family: "Classic Console"; font-size: 16px;
    background: #efc7d1; border-bottom: 1px solid #171717; padding: 8px 12px; }
.paperbit-calendar-card calendar { background: #ffffff; padding: 10px; border: none; }
.paperbit-calendar-card calendar:selected { background: #efc7d1; color: #171717; }
.paperbit-calendar-card calendar.header { background: #f2f2f2; }
.paperbit-calendar-card button { border-radius: 0; border: 1px solid #171717;
    background: #ffffff; padding: 5px 10px; box-shadow: none; }
.paperbit-calendar-card button:hover { background: #efc7d1; }
.paperbit-calendar-card button.calendar-nav { padding: 2px 5px; }
.paperbit-calendar-card .calendar-weekday { padding: 5px 0; font-size: 11px; }
.paperbit-calendar-card button.calendar-day { padding: 4px 0; min-height: 22px;
    border: 2px solid transparent; box-shadow: none; }
.paperbit-calendar-card .weekday { background: #ffffff; }
.paperbit-calendar-card .friday { background: #f8e3ea; }
.paperbit-calendar-card .weekend { background: #e49ab5; }
.paperbit-calendar-card button.calendar-day.weekday { background: #ffffff; }
.paperbit-calendar-card button.calendar-day.friday { background: #f8e3ea; }
.paperbit-calendar-card button.calendar-day.weekend { background: #e49ab5; }
.paperbit-calendar-card button.calendar-day:hover { border-color: #884258; }
.paperbit-calendar-card button.calendar-day.selected-day { border-color: #171717; }
.paperbit-calendar-card button.calendar-day.today label { font-weight: bold; }
.paperbit-calendar-card button.calendar-day.other-month label { opacity: 0.4; }
'''))
Gtk.StyleContext.add_provider_for_screen(window.get_screen(),css,Gtk.STYLE_PROVIDER_PRIORITY_USER+50)

fixed=Gtk.Fixed()
backdrop=Gtk.EventBox()
backdrop.get_style_context().add_class('paperbit-calendar-backdrop')
backdrop.add(fixed)
window.add(backdrop)
card=Gtk.EventBox()
card.get_style_context().add_class('paperbit-calendar-card')
content=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=0)
content.set_size_request(width-4,-1)
card.add(content)
heading=Gtk.Label(label='CALENDARIO',xalign=0)
heading.get_style_context().add_class('calendar-heading')
content.pack_start(heading,False,False,0)
calendar=MonthGrid()
content.pack_start(calendar,True,True,0)
footer=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=8)
footer.set_margin_start(10);footer.set_margin_end(10);footer.set_margin_bottom(10)
today_button=Gtk.Button(label='Hoy')
close_button=Gtk.Button(label='Cerrar')
footer.pack_start(today_button,True,True,0);footer.pack_start(close_button,False,False,0)
content.pack_start(footer,False,False,0)
fixed.put(card,x,y)

def today(*unused):
    calendar.go_today()

def close(*unused):
    Gtk.main_quit();return False

def outside(widget,event):
    source=Gtk.get_event_widget(event)
    if source is card or (source is not None and source.is_ancestor(card)):return False
    close();return True

def key(widget,event):
    if event.keyval==Gdk.KEY_Escape:close();return True
    return False

today_button.connect('clicked',today)
close_button.connect('clicked',close)
backdrop.connect('button-press-event',outside)
window.connect('key-press-event',key)
window.connect('destroy',close)
GLib.unix_signal_add(GLib.PRIORITY_DEFAULT,signal.SIGUSR1,close)
today()
window.show_all()
calendar.grab_focus()
print(f'Calendario: {screen["name"]}, debajo de la barra en ({x}, {y})',flush=True)
Gtk.main()
