#!/usr/bin/env python3
"""Reload Paperbit in the existing Hyprland session, without logging out."""
import json
import os
from pathlib import Path
import signal
import subprocess

instances=json.loads(subprocess.check_output(['hyprctl','-j','instances']))
if not instances:
    raise SystemExit('No hay una sesión de Hyprland activa. Los archivos están preparados para el próximo inicio.')
instance=instances[0]
env=os.environ.copy()
for entry in Path(f'/proc/{instance["pid"]}/environ').read_bytes().split(b'\0'):
    if b'=' in entry:
        k,v=entry.split(b'=',1)
        env[k.decode()]=v.decode()
env.update(WAYLAND_DISPLAY=instance['wl_socket'],HYPRLAND_INSTANCE_SIGNATURE=instance['instance'],
           QT_QPA_PLATFORMTHEME='kde',QT_STYLE_OVERRIDE='Windows',XCURSOR_THEME='Breeze_Light')
env.setdefault('DBUS_SESSION_BUS_ADDRESS',f'unix:path=/run/user/{os.getuid()}/bus')
subprocess.run(['sh','/home/marcos/.local/share/paperbit/session.sh'],env=env,check=True)
subprocess.run(['hyprctl','reload'],env=env,check=True)
subprocess.run(['hyprctl','setcursor','Breeze_Light','24'],env=env,check=True)
subprocess.run(['makoctl','reload'],env=env,check=True)
subprocess.run(['pkill','-USR1','-u',str(os.getuid()),'-x','kitty'],env=env)
# Restart only the bars in this compositor session.
layers=json.loads(subprocess.check_output(['hyprctl','-j','layers'],env=env))
pids={layer['pid'] for monitor in layers.values() for level in monitor['levels'].values()
      for layer in level if layer['namespace']=='waybar'}
for pid in pids:
    try: os.kill(pid,signal.SIGTERM)
    except ProcessLookupError: pass
log=Path('/home/marcos/.local/state/paperbit/waybar.log')
log.parent.mkdir(parents=True,exist_ok=True)
with log.open('w') as out:
    subprocess.Popen(['sh','/home/marcos/.local/share/paperbit/waybar-start.sh'],env=env,
                     stdout=out,stderr=out,start_new_session=True)
print('Hyprland, Kitty, Waybar y Mako recargados. Las aplicaciones Qt abiertas pueden requerir volver a abrirse.')
