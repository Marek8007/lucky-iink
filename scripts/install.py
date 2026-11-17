#!/usr/bin/env python3
"""Link the versioned configuration into HOME, keeping a reversible snapshot."""
import argparse
import datetime
import json
import os
from pathlib import Path
import shutil

REPO=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--home',type=Path,default=Path.home(),help='Target home; useful for a staged install')
parser.add_argument('--dry-run',action='store_true',help='List links without changing anything')
args=parser.parse_args()
home=args.home.expanduser().resolve()
source_home=json.loads((REPO/'snapshot.json').read_text())['source_home']
sources=sorted(p for p in (REPO/'home').rglob('*') if p.is_file() and '__pycache__' not in p.parts)
backup=home/'.local/state/lucky-iink/backups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
manifest={'repository':str(REPO),'home':str(home),'files':[]}
for source in sources:
    relative=source.relative_to(REPO/'home')
    target=home/relative
    # The original machine links directly to tracked files. On another account,
    # rendered files stay inside this repository and are ignored by Git.
    installed=source
    if str(home)!=source_home:
        try:
            text=source.read_text()
        except UnicodeError:
            text=None
        if text is not None and source_home in text:
            installed=REPO/'.generated'/home.name/relative
            if not args.dry_run:
                installed.parent.mkdir(parents=True,exist_ok=True)
                installed.write_text(text.replace(source_home,str(home)))
                shutil.copymode(source,installed)
    if target.is_symlink() and target.resolve()==installed.resolve():continue
    if args.dry_run:
        print(f'{target} -> {installed}')
        continue
    entry={'path':str(relative),'installed_link':str(installed),'previous':'missing'}
    if target.is_symlink():
        entry.update(previous='symlink',link=os.readlink(target))
    elif target.exists():
        if not target.is_file():raise SystemExit(f'Expected a file, found a directory: {target}')
        saved=backup/'files'/relative
        saved.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(target,saved)
        entry['previous']='file'
    manifest['files'].append(entry)
    backup.mkdir(parents=True,exist_ok=True)
    (backup/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    target.parent.mkdir(parents=True,exist_ok=True)
    temp=target.with_name(target.name+'.lucky-iink-link')
    if temp.is_symlink():temp.unlink()
    temp.symlink_to(installed)
    os.replace(temp,target)
if args.dry_run:
    print(f'Dry run: {len(sources)} source files inspected.')
elif manifest['files']:
    state=home/'.local/state/lucky-iink'
    (state/'last-backup').write_text(str(backup)+'\n')
    print(f'Installed {len(manifest["files"])} links. Backup: {backup}')
else:
    print('Everything is already linked to this repository.')
