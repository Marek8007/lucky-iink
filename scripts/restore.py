#!/usr/bin/env python3
"""Restore the files replaced by a lucky-iink installation."""
import argparse
import json
import os
from pathlib import Path
import shutil

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('backup',nargs='?',type=Path)
parser.add_argument('--home',type=Path,default=Path.home())
args=parser.parse_args()
home=args.home.expanduser().resolve()
backup=args.backup or Path((home/'.local/state/lucky-iink/last-backup').read_text().strip())
manifest=json.loads((backup/'manifest.json').read_text())
if Path(manifest['home']).resolve()!=home:raise SystemExit('This backup belongs to a different home directory.')
restored=0
for entry in reversed(manifest['files']):
    relative=Path(entry['path'])
    if relative.is_absolute() or '..' in relative.parts:raise SystemExit('Invalid backup path')
    target=home/relative
    if not target.is_symlink() or os.readlink(target)!=entry['installed_link']:
        print(f'Skipped changed file: {target}')
        continue
    target.unlink()
    if entry['previous']=='file':shutil.copy2(backup/'files'/relative,target)
    elif entry['previous']=='symlink':target.symlink_to(entry['link'])
    restored+=1
print(f'Restored {restored} paths. Reload your session components to apply.')
