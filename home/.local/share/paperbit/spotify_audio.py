"""One CAVA analyser shared by all desktop panels, monitoring Spotify's output only."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
from gi.repository import Gio, GLib

class SpotifyAudio:
    def __init__(self):
        self.bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        self.levels = [0] * 24
        self.title, self.artist, self.status = 'Spotify', 'Abre Spotify para escuchar música', 'Stopped'
        self.position, self.duration = 0, 1
        self.processes, self.stream, self.watch = [], None, None
        self.directory = tempfile.TemporaryDirectory(prefix='paperbit-audio-', dir=os.environ['XDG_RUNTIME_DIR'])
        self.fifo = Path(self.directory.name)/'audio.pcm'
        os.mkfifo(self.fifo, 0o600)
        self.keepalive = os.open(self.fifo, os.O_RDWR | os.O_NONBLOCK)
        self.config = Path(self.directory.name)/'cava.conf'
        self.config.write_text(f'''[general]
framerate = 24
bars = 24
autosens = 1
[input]
method = fifo
source = {self.fifo}
sample_rate = 44100
sample_bits = 16
[output]
method = raw
raw_target = /dev/stdout
data_format = binary
bit_format = 8bit
channels = mono
[smoothing]
noise_reduction = 65
''')
        self.timer = GLib.timeout_add_seconds(1, self.update)
        self.update()

    def stop(self):
        if self.watch:
            GLib.source_remove(self.watch)
            self.watch = None
        for p in self.processes:
            if p.poll() is None:
                p.terminate()
        for p in self.processes:
            try: p.wait(timeout=1)
            except subprocess.TimeoutExpired: p.kill(); p.wait()
        self.processes = []
        self.stream = None
        self.levels = [0]*24
        while True:
            try:
                if not os.read(self.keepalive, 65536): break
            except BlockingIOError: break

    def start(self, stream, source):
        self.stop()
        cava = subprocess.Popen(['cava','-p',str(self.config)], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        with self.fifo.open('wb', buffering=0) as audio:
            recorder = subprocess.Popen(['parec','--raw','--format=s16le','--rate=44100','--channels=2',
                '--client-name=Paperbit Spotify Visualizer',f'--device={source}',f'--monitor-stream={stream}'],
                stdout=audio, stderr=subprocess.DEVNULL)
        self.processes = [cava, recorder]
        self.stream = (stream, source)
        self.buffer = b''
        os.set_blocking(cava.stdout.fileno(), False)
        self.watch = GLib.io_add_watch(cava.stdout.fileno(), GLib.IO_IN | GLib.IO_HUP, self.read)

    def read(self, fd, condition):
        if condition & GLib.IO_HUP:
            self.watch = None
            return False
        try: self.buffer += os.read(fd, 65536)
        except BlockingIOError: return True
        frames = len(self.buffer)//24
        if frames:
            self.levels = list(self.buffer[(frames-1)*24:frames*24])
            self.buffer = self.buffer[frames*24:]
        return True

    def update(self):
        try:
            result = self.bus.call_sync('org.mpris.MediaPlayer2.spotify','/org/mpris/MediaPlayer2',
                'org.freedesktop.DBus.Properties','GetAll',GLib.Variant('(s)',('org.mpris.MediaPlayer2.Player',)),
                None,Gio.DBusCallFlags.NONE,500,None).unpack()[0]
            metadata = result.get('Metadata',{})
            self.title = metadata.get('xesam:title','Sin canción')
            self.artist = ' · '.join(metadata.get('xesam:artist',[]))
            self.status = result.get('PlaybackStatus','Stopped')
            self.position = result.get('Position',0)
            self.duration = max(1, metadata.get('mpris:length',1))
        except GLib.Error:
            self.title,self.artist,self.status = 'Spotify','Abre Spotify para escuchar música','Stopped'
        target = None
        if self.status == 'Playing':
            try:
                streams = json.loads(subprocess.check_output(['pactl','--format=json','list','sink-inputs'],timeout=1,stderr=subprocess.DEVNULL))
                sinks = json.loads(subprocess.check_output(['pactl','--format=json','list','sinks'],timeout=1,stderr=subprocess.DEVNULL))
                for s in streams:
                    props=s.get('properties',{})
                    if 'spotify' in (props.get('application.name','')+' '+props.get('application.id','')).lower():
                        sink = next((v for v in sinks if v['index']==s['sink']),None)
                        if sink: target = (s['index'],sink['monitor_source'])
                        break
            except (subprocess.SubprocessError, ValueError): pass
        if target != self.stream or (target and any(p.poll() is not None for p in self.processes)):
            if target: self.start(*target)
            else: self.stop()
        return True

    def close(self):
        GLib.source_remove(self.timer)
        self.stop()
        os.close(self.keepalive)
        self.directory.cleanup()
