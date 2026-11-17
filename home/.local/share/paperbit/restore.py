#!/usr/bin/env python3
"""Restore a Paperbit snapshot. Optional first argument: snapshot directory."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

root=Path('/home/marcos')
backup=Path(sys.argv[1]) if len(sys.argv)>1 else Path((root/'.local/share/paperbit/original-backup').read_text().strip())
manifest=json.loads((backup/'manifest.json').read_text())
for rel,existed in manifest.items():
    target=root/rel
    if existed:
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(backup/rel,target)
    elif target.is_file():
        target.unlink()
for key,value in json.loads((backup/'gsettings.json').read_text()).items():
    subprocess.run(['gsettings','set','org.gnome.desktop.interface',key,value],check=True)
instances=json.loads(subprocess.check_output(['hyprctl','-j','instances']))
for instance in instances:
    subprocess.run(['hyprctl','-i',instance['instance'],'reload'],check=True)
subprocess.run(['pkill','-USR1','-u',str(__import__('os').getuid()),'-x','kitty'])
print('Configuración anterior restaurada. Vuelve a iniciar sesión para recargar todos los componentes.')
