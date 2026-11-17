"""Shared, cached Open-Meteo weather; network requests run outside GTK's thread."""
import datetime
import html
import json
from pathlib import Path
import threading
import time
import urllib.parse
import urllib.request
import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk,GLib

ROOT=Path('/home/marcos/.local/share/paperbit')
CACHE=Path('/home/marcos/.local/state/paperbit/weather-cache.json')

def description(code):
    if code==0:return 'Despejado'
    if code in (1,2):return 'Parcialmente nublado'
    if code==3:return 'Cubierto'
    if code in (45,48):return 'Niebla'
    if code in (51,53,55,56,57):return 'Llovizna'
    if code in (61,63,65,66,67,80,81,82):return 'Lluvia'
    if code in (71,73,75,77,85,86):return 'Nieve'
    if code in (95,96,99):return 'Tormenta'
    return 'Estado no disponible'

def ascii_markup(art,code):
    """Color ASCII cells as well as their glyphs, using Paperbit's small palette."""
    lines=art.splitlines()
    width=max(map(len,lines))
    output=[]
    for row,line in enumerate(lines):
        cells=[]
        first=line.find('(');last=line.rfind(')')
        for col,char in enumerate(line.ljust(width)):
            bg,fg='#ffffff','#884258'
            if first>=0 and first<=col<=last:
                bg='#efc7d1' if row<2 else '#f2f2f2'
                fg='#171717'
            if char in '._-':
                bg='#efc7d1' if row==0 else '#171717'
                fg='#171717' if row==0 else '#efc7d1'
            if char in '/\\|*Z':
                bg='#efc7d1' if row==2 else '#f2f2f2'
            if code==0 and char in '()':
                bg,fg='#efc7d1','#171717'
            cells.append(f'<span foreground="{fg}" background="{bg}">{html.escape(char)}</span>')
        output.append(''.join(cells))
    return '\n'.join(output)

class WeatherService:
    def __init__(self):
        self.config=json.loads((ROOT/'weather.json').read_text())
        self.data=None
        self.error=False
        try:
            cached=json.loads(CACHE.read_text())
            if cached.get('location')==self.config: self.data=cached
        except (OSError,ValueError):pass
        threading.Thread(target=self.worker,daemon=True).start()
    def worker(self):
        while True:
            try:
                query=urllib.parse.urlencode({
                    'latitude':self.config['latitude'],'longitude':self.config['longitude'],
                    'timezone':self.config['timezone'],'forecast_days':1,
                    'current':'temperature_2m,apparent_temperature,weather_code,wind_speed_10m',
                    'daily':'temperature_2m_max,temperature_2m_min',
                })
                request=urllib.request.Request('https://api.open-meteo.com/v1/forecast?'+query,headers={'User-Agent':'Paperbit desktop weather'})
                with urllib.request.urlopen(request,timeout=12) as response: data=json.load(response)
                current=data['current'];daily=data['daily']
                self.data={'location':self.config,'fetched_at':time.time(),
                    'temperature':current['temperature_2m'],'feels':current['apparent_temperature'],
                    'wind':current['wind_speed_10m'],'code':current['weather_code'],
                    'max':daily['temperature_2m_max'][0],'min':daily['temperature_2m_min'][0]}
                CACHE.write_text(json.dumps(self.data))
                self.error=False
                time.sleep(max(5,int(self.config['refresh_minutes']))*60)
            except (OSError,ValueError,KeyError,TypeError) as error:
                self.error=True
                print('Weather:',error,flush=True)
                time.sleep(60)

class Weather(Gtk.Box):
    def __init__(self,service):
        super().__init__(orientation=Gtk.Orientation.VERTICAL,spacing=2)
        self.service=service
        self.set_margin_start(12);self.set_margin_end(12)
        self.set_margin_top(6);self.set_margin_bottom(5)
        row=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=10)
        self.art=Gtk.Label(xalign=0)
        self.art.get_style_context().add_class('weather-ascii')
        row.pack_start(self.art,False,False,0)
        info=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=1)
        self.summary=Gtk.Label(xalign=0)
        self.details=Gtk.Label(xalign=0)
        self.range=Gtk.Label(xalign=0)
        self.source=Gtk.Label(xalign=1)
        for label in (self.summary,self.details,self.range):
            label.set_ellipsize(3)
            info.pack_start(label,False,False,0)
        row.pack_start(info,True,True,0)
        self.pack_start(row,True,True,0)
        self.pack_start(self.source,False,False,0)
        self.refresh()
        self.timer=GLib.timeout_add_seconds(20,self.refresh)
        self.connect('destroy',lambda *args:GLib.source_remove(self.timer))
    def refresh(self):
        data=self.service.data
        self.set_tooltip_text('Datos meteorológicos: Open-Meteo · https://open-meteo.com/\nActualización cada 15 minutos')
        if not data:
            self.art.set_text('  .--.\n (    )\n  ----')
            self.summary.set_text(self.service.config['city'])
            self.details.set_text('Sin conexión' if self.service.error else 'Consultando el tiempo…')
            self.source.set_markup('<span size="small" foreground="#626262">Open-Meteo</span>')
        else:
            code=data['code']
            if code==0:
                art=' \\ | /\n--( )--\n / | \\'
            elif code in (1,2):
                art=' \\ | /\n _ .--.\n(______)'
            elif code in (51,53,55,56,57,61,63,65,66,67,80,81,82):
                art='  .--.\n (____)\n / / /'
            elif code in (95,96,99):
                art='  .--.\n (____)\n  /Z /'
            elif code in (71,73,75,77,85,86):
                art='  .--.\n (____)\n * * *'
            elif code in (45,48):
                art=' -----\n-------\n -----'
            else:
                art='  .--.\n (    ).\n(___(__)'
            self.art.set_markup(ascii_markup(art,code))
            self.summary.set_markup(f'<span foreground="#884258" weight="bold">{data["temperature"]:.0f}°</span> · '+description(code))
            self.details.set_text(f'Sens {data["feels"]:.0f}° · {data["wind"]:.0f} km/h')
            self.range.set_text(f'Mín {data["min"]:.0f}° / Máx {data["max"]:.0f}°')
            stamp=datetime.datetime.fromtimestamp(data['fetched_at']).strftime('%H:%M')
            stale=' · sin actualizar' if self.service.error or time.time()-data['fetched_at']>1800 else ''
            self.source.set_markup(f'<span foreground="#626262">Open-Meteo · {stamp}{stale}</span>')
        return True
