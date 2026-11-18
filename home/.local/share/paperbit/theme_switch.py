#!/usr/bin/env python3
"""Switch Paperbit's saved visual profiles without changing functional settings."""
import argparse
import configparser
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import time
from theme_support import DARK_COLORS,tint

HOME_DIR=Path.home()
ROOT=HOME_DIR/'.local/share/paperbit'
PROFILE=ROOT/'themes/light'
FILES=[
    '.config/hypr/paperbit.lua','.config/hypr/hyprlock.conf','.config/hypr/hyprtoolkit.conf',
    '.config/waybar/style.css','.config/wofi/style.css','.config/mako/config',
    '.config/kdeglobals','.local/share/color-schemes/Paperbit.colors',
    '.local/share/paperbit/widgets/themes/Paperbit.theme','.config/fastfetch/paperbit.json',
    '.config/kitty/paperbit.conf',
]
for version in ('3.0','4.0'):
    FILES += [f'.config/gtk-{version}/{name}' for name in
        ('settings.ini','colors.css','gtk.css','window_decorations.css')]
FILES += [str(p.relative_to(HOME_DIR)) for p in (HOME_DIR/'.local/share/icons/Paperbit').rglob('*.svg')]

def current_mode():
    try:return json.loads((ROOT/'theme.json').read_text()).get('mode','light')
    except (OSError,ValueError):return 'light'

def preferences(mode):
    values={'color-scheme':'prefer-dark' if mode=='dark' else 'prefer-light',
        'gtk-theme':'Breeze','icon-theme':'Paperbit','cursor-theme':'Breeze_Light','font-name':'Noto Sans 10'}
    for key,value in values.items():
        subprocess.run(['gsettings','set','org.gnome.desktop.interface',key,value],check=True)

def create_profile():
    if (PROFILE/'manifest.json').exists():return
    if current_mode()!='light':raise RuntimeError('Primero debe guardarse la versión clara.')
    for relative in FILES:
        source=HOME_DIR/relative
        if not source.is_file():raise FileNotFoundError(source)
        target=PROFILE/'files'/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,target)
    (PROFILE/'manifest.json').write_text(json.dumps(FILES,indent=2)+'\n')

def dark_content(relative,text):
    if relative=='.config/kitty/paperbit.conf':
        # Kitty already uses a dark palette to keep true-color TUI programs readable.
        return text.replace('inactive_tab_background #f2f2f2','inactive_tab_background #242424').replace('inactive_tab_foreground #626262','inactive_tab_foreground #b8b8b8')
    text=tint(text,True)
    text=re.sub(r'rgba\(([0-9a-fA-F]{6})([0-9a-fA-F]{2})\)',
        lambda m:'rgba('+DARK_COLORS.get('#'+m[1].lower(),'#'+m[1])[1:]+m[2]+')',text)
    text=re.sub(r'0xFF([0-9a-fA-F]{6})\b',
        lambda m:'0xFF'+DARK_COLORS.get('#'+m[1].lower(),'#'+m[1])[1:],text)
    def rgb_line(m):
        old='#'+''.join(f'{int(m[i]):02x}' for i in (2,3,4))
        value=DARK_COLORS.get(old,old)
        return m[1]+','.join(str(int(value[i:i+2],16)) for i in (1,3,5))
    text=re.sub(r'^(\w+=)(\d+),(\d+),(\d+)$',rgb_line,text,flags=re.M)
    text=text.replace('gtk-application-prefer-dark-theme=false','gtk-application-prefer-dark-theme=true')
    if relative=='.config/kdeglobals':text=text.replace('org.kde.breeze.desktop','org.kde.breezedark.desktop')
    if relative=='.config/fastfetch/paperbit.json':
        text=text.replace('38;2;163;79;112','38;2;231;166;189').replace('38;2;136;66;88','38;2;231;166;189')
    return text

def stop_apps(names):
    stopped=[]
    for path in Path('/proc').iterdir():
        if not path.name.isdigit():continue
        try:
            if path.stat().st_uid!=os.getuid():continue
            args=(path/'cmdline').read_bytes().split(b'\0')
        except OSError:continue
        if len(args)>1 and args[0].endswith(b'python3') and args[1].decode() in names:
            try:os.kill(int(path.name),signal.SIGTERM);stopped.append(path)
            except ProcessLookupError:pass
    deadline=time.monotonic()+3
    while time.monotonic()<deadline and any(p.exists() for p in stopped):time.sleep(.05)

def reload_components():
    instances=json.loads(subprocess.check_output(['hyprctl','-j','instances']))
    if not instances:return
    instance=instances[0];env=os.environ.copy()
    for entry in Path(f'/proc/{instance["pid"]}/environ').read_bytes().split(b'\0'):
        if b'=' in entry:
            key,value=entry.split(b'=',1);env[key.decode()]=value.decode()
    env.update(WAYLAND_DISPLAY=instance['wl_socket'],GDK_BACKEND='wayland',HYPRLAND_INSTANCE_SIGNATURE=instance['instance'])
    stop_apps([str(ROOT/name) for name in ('wallpaper.py','desktop_widgets.py','calendar_popup.py')])
    state=HOME_DIR/'.local/state/paperbit';state.mkdir(parents=True,exist_ok=True)
    for name,logname in [('wallpaper.py','wallpaper.log'),('desktop_widgets.py','widgets.log')]:
        with (state/logname).open('w') as log:
            subprocess.Popen(['python3',str(ROOT/name)],env=env,stdout=log,stderr=log,start_new_session=True)
    subprocess.run(['python3',str(ROOT/'reload.py')],env=env,check=True)

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('mode',nargs='?',choices=['toggle','light','dark'],default='toggle')
parser.add_argument('--init',action='store_true',help='Capture the current light styles without switching')
parser.add_argument('--preferences',action='store_true',help='Apply only desktop appearance preferences')
parser.add_argument('--no-reload',action='store_true')
args=parser.parse_args()
if args.preferences:
    preferences(current_mode());raise SystemExit(0)
lock=open(Path(os.environ.get('XDG_RUNTIME_DIR','/tmp'))/f'paperbit-theme-{os.getuid()}.lock','w')
try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
except BlockingIOError:raise SystemExit(0)
create_profile()
if args.init:print('Perfil claro guardado.');raise SystemExit(0)
mode=('dark' if current_mode()=='light' else 'light') if args.mode=='toggle' else args.mode
for relative in json.loads((PROFILE/'manifest.json').read_text()):
    text=(PROFILE/'files'/relative).read_text()
    (HOME_DIR/relative).write_text(dark_content(relative,text) if mode=='dark' else text)
wallpaper=json.loads((ROOT/'wallpaper.json').read_text())
wallpaper['background']='#171717' if mode=='dark' else '#ffffff'
(ROOT/'wallpaper.json').write_text(json.dumps(wallpaper,ensure_ascii=False,indent=2)+'\n')
(ROOT/'theme.json').write_text(json.dumps({'mode':mode},indent=2)+'\n')
preferences(mode)
if not args.no_reload:reload_components()
print('Paperbit oscuro' if mode=='dark' else 'Paperbit claro')
