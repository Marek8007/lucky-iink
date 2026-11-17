#!/usr/bin/env python3
"""Real desktop-layer panels: fastfetch, btop and Spotify/CAVA on every monitor."""
import ctypes as C
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import gi

gi.require_version('Gtk','3.0')
gi.require_version('Vte','2.91')
from gi.repository import Gtk,Gdk,GdkPixbuf,GLib,Pango,Vte
from spotify_audio import SpotifyAudio
from weather_widget import WeatherService,Weather

ROOT=Path('/home/marcos/.local/share/paperbit')
lock=open(Path(os.environ['XDG_RUNTIME_DIR'])/'paperbit-desktop-widgets.lock','w')
try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
except BlockingIOError: raise SystemExit(0)
lib=C.CDLL('libgtk-layer-shell.so.0')
capsule=C.pythonapi.PyCapsule_GetPointer
capsule.argtypes=[C.py_object,C.c_char_p];capsule.restype=C.c_void_p
def ptr(obj): return capsule(obj.__gpointer__,None)
def api(name,args):
    f=getattr(lib,'gtk_layer_'+name);f.argtypes=args;f.restype=None;return f
init=api('init_for_window',[C.c_void_p])
set_layer=api('set_layer',[C.c_void_p,C.c_int])
set_monitor=api('set_monitor',[C.c_void_p,C.c_void_p])
anchor=api('set_anchor',[C.c_void_p,C.c_int,C.c_int])
margin=api('set_margin',[C.c_void_p,C.c_int,C.c_int])
zone=api('set_exclusive_zone',[C.c_void_p,C.c_int])
keyboard=api('set_keyboard_mode',[C.c_void_p,C.c_int])
namespace=api('set_namespace',[C.c_void_p,C.c_char_p])
def color(hex):
    c=Gdk.RGBA();c.parse(hex);return c

css=Gtk.CssProvider()
css.load_from_data(b'''
window.paperbit-panel { background: #ffffff; color: #171717; border: 2px solid #171717; }
.paperbit-weather label { font-family: "JetBrainsMono Nerd Font", monospace; font-size: 10px; }
.paperbit-weather .paperbit-heading { font-family: "Classic Console"; font-size: 14px; }
.paperbit-weather .weather-ascii { color: #884258; font-family: "JetBrainsMono Nerd Font", monospace; font-size: 11px; }
.paperbit-heading { font-family: "Classic Console"; font-size: 16px;
 padding: 5px 10px; color: #171717; background: #f2f2f2; border-bottom: 1px solid #171717; }
.paperbit-title { font-family: "JetBrainsMono Nerd Font"; font-size: 12px; font-weight: bold; color: #171717; }
.paperbit-artist { font-family: "JetBrainsMono Nerd Font"; font-size: 10px; color: #626262; }
''')
Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(),css,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION+20)
audio=SpotifyAudio()
weather=WeatherService()
panels=[]
children=set()

def make_panel(screen,name,title,x,y,width,height):
    win=Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
    win.get_style_context().add_class('paperbit-panel')
    win.get_style_context().add_class('paperbit-'+name)
    win.set_accept_focus(False)
    win.set_size_request(width,height)
    init(ptr(win));set_layer(ptr(win),1);set_monitor(ptr(win),ptr(screen))
    namespace(ptr(win),('paperbit-'+name).encode())
    zone(ptr(win),-1);keyboard(ptr(win),0)
    anchor(ptr(win),2,True);anchor(ptr(win),0,True)
    margin(ptr(win),2,y);margin(ptr(win),0,x)
    box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    heading=Gtk.Label(label=title,xalign=0)
    heading.get_style_context().add_class('paperbit-heading')
    box.pack_start(heading,False,False,0)
    win.add(box)
    panels.append(win)
    return win,box

def terminal(box,args,font,on_exit=None):
    term=Vte.Terminal()
    term.set_font(Pango.FontDescription('JetBrainsMono Nerd Font '+str(font)))
    term.set_color_background(color('#ffffff'));term.set_color_foreground(color('#171717'))
    term.set_colors(color('#171717'),color('#ffffff'),[color(v) for v in [
        '#171717','#884258','#404040','#66545a','#444444','#884258','#626262','#aaaaaa',
        '#626262','#884258','#171717','#884258','#171717','#884258','#444444','#171717']])
    term.set_scrollback_lines(0)
    term.set_color_cursor(color('#ffffff'))
    term.set_input_enabled(False)
    term.set_can_focus(False)
    term.set_margin_start(10);term.set_margin_end(10)
    term.set_margin_top(10);term.set_margin_bottom(8)
    box.pack_start(term,True,True,0)
    def spawned(t,pid,error,*unused):
        if error: print('Terminal spawn error:',error,flush=True)
        elif pid>0:
            children.add(pid)
            t._child_pid=pid
    def exited(t,status):
        children.discard(getattr(t,'_child_pid',None))
        t._child_pid=None
        t.feed(b'\x1b[?25l')
        if on_exit: GLib.idle_add(on_exit,t)
    def destroyed(t):
        pid=getattr(t,'_child_pid',None)
        if pid in children:
            try: os.kill(pid,signal.SIGTERM)
            except ProcessLookupError: pass
            children.discard(pid)
    term.connect('child-exited',exited)
    term.connect('destroy',destroyed)
    def spawn():
        term.spawn_async(pty_flags=Vte.PtyFlags.DEFAULT,working_directory=str(ROOT),argv=args,
            envv=['TERM=xterm-256color'],spawn_flags=GLib.SpawnFlags.DEFAULT,child_setup=None,
            timeout=-1,cancellable=None,callback=spawned,user_data=None)
        return False
    GLib.timeout_add(300,spawn)
    return term

class Music(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL,spacing=5)
        self.set_margin_start(14);self.set_margin_end(14)
        self.set_margin_top(12);self.set_margin_bottom(10)
        self.title=Gtk.Label(xalign=0);self.title.set_ellipsize(Pango.EllipsizeMode.END)
        self.title.get_style_context().add_class('paperbit-title')
        self.artist=Gtk.Label(xalign=0);self.artist.set_ellipsize(Pango.EllipsizeMode.END)
        self.artist.get_style_context().add_class('paperbit-artist')
        self.pack_start(self.title,False,False,0);self.pack_start(self.artist,False,False,0)
        self.graph=Gtk.DrawingArea();self.graph.set_vexpand(True)
        self.graph.connect('draw',self.draw);self.pack_start(self.graph,True,True,0)
        self.timer=GLib.timeout_add(42,self.refresh)
        self.connect('destroy',lambda *args: GLib.source_remove(self.timer))
    def refresh(self):
        self.title.set_text(audio.title)
        status='EN PAUSA · ' if audio.status=='Paused' else ''
        self.artist.set_text(status+audio.artist)
        self.graph.queue_draw();return True
    def draw(self,widget,cr):
        width,height=widget.get_allocated_width(),widget.get_allocated_height()
        max_h=max(8,height-26);step=width/24
        for i,level in enumerate(audio.levels):
            blocks=max(1,int((level/255)*max_h/5))
            for block in range(blocks):
                cr.set_source_rgb(*((0.937,0.780,0.820) if block==blocks-1 else (0.09,0.09,0.09)))
                cr.rectangle(int(i*step),max_h-block*5,max(2,int(step)-3),3);cr.fill()
        cr.set_source_rgb(0.85,0.85,0.85);cr.rectangle(0,height-8,width,2);cr.fill()
        if audio.status!='Stopped':
            cr.set_source_rgb(0.53,0.26,0.35)
            cr.rectangle(0,height-8,width*min(1,audio.position/audio.duration),2);cr.fill()

screens={}
def add_monitor(display,screen):
    first_panel=len(panels)
    geom=screen.get_geometry();w,h=geom.width,geom.height
    side=max(300,int(w*0.28));left=24
    top=70
    font=6 if w<1500 else 8
    fetch_h=min(int(h*0.68),760)
    fetch_y=max(54,(h-fetch_h)//2-54)
    # Music stays beneath the artwork, near the bottom with a small margin.
    artwork=json.loads((ROOT/'wallpaper.json').read_text())
    artwork_size=int(artwork.get('size',320))
    music_y=(h+artwork_size)//2+24
    music_x=max(left+side+24,(w-artwork_size)//2)
    music_w=w-music_x-24
    music_h=max(120,min(int(h*0.25),h-music_y-24))
    music_y=h-music_h-16
    btop_w=int(w*0.34)
    btop_x=w-btop_w-24
    weather_w=320
    weather_h=112
    weather_x=left+(side-weather_w)//2
    weather_y=music_y-weather_h-16
    btop_h=weather_y-top-16
    weather_y+=50
    win,box=make_panel(screen,'fetch','01 / SYSTEM',left,fetch_y,side,fetch_h)
    fetch_settings=json.loads((ROOT/'fetch.json').read_text())
    image_path=Path(fetch_settings['image']).expanduser()
    image=None
    try:
        pixbuf=GdkPixbuf.Pixbuf.new_from_file(str(image_path))
        target_h=min(int(fetch_settings.get('image_height',96)),int(fetch_h*0.22))
        factor=min((side-32)/pixbuf.get_width(),target_h/pixbuf.get_height())
        interpolation=GdkPixbuf.InterpType.NEAREST if fetch_settings.get('pixel_art') else GdkPixbuf.InterpType.BILINEAR
        pixbuf=pixbuf.scale_simple(max(1,int(pixbuf.get_width()*factor)),max(1,int(pixbuf.get_height()*factor)),interpolation)
        image=Gtk.Image.new_from_pixbuf(pixbuf)
        image.set_margin_top(12)
        box.pack_start(image,False,False,0)
    except (GLib.Error,OSError) as error:
        print('Fetch image:',error,flush=True)
    fetch_window,fetch_box=win,box
    weather_window,weather_box=make_panel(screen,'weather','04 / TIEMPO - '+weather.config['city'].upper(),weather_x,weather_y,weather_w,weather_h)
    weather_box.pack_start(Weather(weather),True,True,0)
    weather_window.show_all()
    def fit_fetch(term):
        text=(term.get_text_format(Vte.Format.TEXT) or '').rstrip()
        # Leave the final cursor row so VTE does not scroll away the first line.
        rows=max(1,len(text.splitlines()))+1
        text_h=rows*term.get_char_height()+18
        other_h=sum(child.get_allocated_height()+child.get_margin_top()+child.get_margin_bottom()
            for child in fetch_box.get_children() if child is not term)
        height=text_h+other_h+4
        # On the laptop, compact the illustration enough to keep the panels apart.
        overlap=fetch_y+height+16-weather_y
        if overlap>0 and image is not None:
            current=image.get_pixbuf()
            old_h=current.get_height()
            new_h=max(24,old_h-overlap)
            new_w=max(1,round(current.get_width()*new_h/old_h))
            image.set_from_pixbuf(current.scale_simple(new_w,new_h,interpolation))
            height-=old_h-new_h
        term.set_size(term.get_column_count(),rows)
        term.set_size_request(-1,rows*term.get_char_height())
        fetch_window.set_size_request(side,height)
        fetch_window.resize(side,height)
        print(f'Fetch ajustado: {height}px; tiempo centrado a la izquierda a {weather_y}px',flush=True)
        return False
    terminal(box,['fastfetch','--config','/home/marcos/.config/fastfetch/paperbit.json'],font+1,on_exit=fit_fetch)
    win.show_all()
    win,box=make_panel(screen,'btop','02 / SYSTEM MONITOR',btop_x,top,btop_w,btop_h)
    terminal(box,['btop','--config',str(ROOT/'widgets/btop.conf'),'--themes-dir',str(ROOT/'widgets/themes')],font)
    win.show_all()
    win,box=make_panel(screen,'music','03 / SPOTIFY',music_x,music_y,music_w,music_h)
    box.pack_start(Music(),True,True,0);win.show_all()
    screens[screen]=panels[first_panel:]
    print(f'Widgets: {screen.get_model()} {w}x{h}, ancho {side}',flush=True)

def remove_monitor(display,screen):
    for win in screens.pop(screen,[]): win.destroy()

def shutdown(*unused):
    audio.close()
    for pid in children:
        try: os.kill(pid,signal.SIGTERM)
        except ProcessLookupError: pass
    Gtk.main_quit();return False

display=Gdk.Display.get_default()
for i in range(display.get_n_monitors()): add_monitor(display,display.get_monitor(i))
display.connect('monitor-added',add_monitor);display.connect('monitor-removed',remove_monitor)
GLib.unix_signal_add(GLib.PRIORITY_DEFAULT,signal.SIGTERM,shutdown)
GLib.unix_signal_add(GLib.PRIORITY_DEFAULT,signal.SIGINT,shutdown)
Gtk.main()
