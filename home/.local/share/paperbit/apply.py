#!/usr/bin/env python3
"""Paperbit: generate a desktop theme; back up each touched file before editing."""
from pathlib import Path
import configparser
import datetime
import io
import json
import re
import shutil
import subprocess

ROOT = Path('/home/marcos')
THEME = ROOT / '.local/share/paperbit'
BACKUP = ROOT / '.local/state/paperbit/backups' / datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
BACKUP.mkdir(parents=True)
manifest = {}
P = {'paper':'#ffffff', 'ink':'#171717', 'surface':'#f2f2f2', 'muted':'#626262',
     'line':'#b8b8b8', 'pink':'#efc7d1', 'rose':'#884258'}
palette = THEME / 'palette.json'
if palette.exists():
    P.update(json.loads(palette.read_text()))
else:
    palette.write_text(json.dumps(P, indent=2) + '\n')

def write(rel, text):
    dest = ROOT / rel
    if rel not in manifest:
        manifest[rel] = dest.exists()
        if dest.exists():
            saved = BACKUP / rel
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dest, saved)
        (BACKUP / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text)

def render(s):
    for key, value in P.items():
        s = s.replace('@'+key+'@', value)
    return s

def cfg(path):
    c = configparser.ConfigParser(interpolation=None, strict=False)
    c.optionxform = str
    c.read(path)
    return c

def save_cfg(rel, c):
    s = io.StringIO(); c.write(s, space_around_delimiters=False)
    write(rel, s.getvalue())

def set_cfg(c, section, values):
    if not c.has_section(section): c.add_section(section)
    for key, value in values.items(): c[section][key] = str(value)

def rgb(key):
    return ','.join(str(int(P[key][i:i+2],16)) for i in (1,3,5))

# Keep geometry and actions in hyprland.lua, appearance in its own Lua module.
hypr_path = ROOT / '.config/hypr/hyprland.lua'
hypr = hypr_path.read_text()
start = hypr.index('    general = {')
end = hypr.index('    dwindle =', start)
hypr = hypr[:start] + '    general = { layout = "dwindle" },\n' + hypr[end:]
if 'require("paperbit")' not in hypr:
    hypr = hypr.replace('\nhl.on("hyprland.start"', '\nrequire("paperbit")\n\nhl.on("hyprland.start"', 1)
if 'paperbit/session.sh' not in hypr:
    hypr = hypr.replace('hl.on("hyprland.start", function()\n', 'hl.on("hyprland.start", function()\n    hl.exec_cmd("sh /home/marcos/.local/share/paperbit/session.sh")\n', 1)
write('.config/hypr/hyprland.lua', hypr)
lua = '''-- Paperbit: aspecto visual. Funciones y monitores en hyprland.lua.
hl.env("QT_QPA_PLATFORMTHEME", "kde")
hl.env("QT_STYLE_OVERRIDE", "Windows")
hl.env("XCURSOR_THEME", "Breeze_Light")
hl.config({
    general = {
        gaps_in = 5, gaps_out = 12, border_size = 2,
        col = { active_border = "INK", inactive_border = "LINE" },
    },
    decoration = {
        rounding = 0, active_opacity = 1.0, inactive_opacity = 1.0,
        blur = { enabled = false }, shadow = { enabled = false },
    },
    animations = { enabled = false },
    misc = {
        disable_hyprland_logo = true, disable_splash_rendering = true,
        background_color = "PAPER",
    },
})
'''
for name in ['ink','line','paper']:
    lua = lua.replace(name.upper(), 'rgba('+P[name][1:]+'ff)')
write('.config/hypr/paperbit.lua', lua)

bar = json.loads((ROOT/'.config/waybar/config.jsonc').read_text())
bar.update(height=34, spacing=0, margin='8 12 0 12')
bar['custom/apps'].update(format='  MENU', tooltip=True, **{'tooltip-format':'Aplicaciones · Win / Win+D'})
bar['custom/terminal'].update(format='[ >_ ]', tooltip=True, **{'tooltip-format':'Terminal · Ctrl+Alt+T'})
bar['custom/session'].update(format='[ salir ]', tooltip=True, **{'tooltip-format':'Bloquear / cerrar sesión / apagar'})
bar['clock'].update(format='{:%d.%m  /  %H:%M:%S}', interval=1)
bar['clock']['on-click']='python3 /home/marcos/.local/share/paperbit/calendar_popup.py'
bar['network'].update({'format-wifi':'NET {signalStrength}%', 'format-ethernet':'NET LAN',
    'format-disconnected':'NET --', 'tooltip-format':'{ifname} · {essid}\n{ipaddr}\nClic: conexiones'})
bar['pulseaudio'].update({'format':'VOL {volume}%', 'format-muted':'VOL --'})
bar['battery'].update({'format':'BAT {capacity}%', 'format-charging':'BAT +{capacity}%'})
bar['tray'].update({'icon-size':16, 'spacing':8})
from spotify_bar import configure as configure_spotify
configure_spotify(bar)
save = json.dumps(bar, ensure_ascii=False, indent=2)+'\n'
write('.config/waybar/config.jsonc',save)
write('.config/waybar/style.css',render('''/* Paperbit: panel compacto, controles existentes, tipografía de píxel. */
* { font-family: "Classic Console", "JetBrainsMono Nerd Font", monospace;
    font-size: 16px; font-weight: normal; border-radius: 0; min-height: 0;
    text-shadow: none; }
window#waybar { background: @paper@; color: @ink@; border: 2px solid @ink@; }
tooltip { background: @paper@; border: 2px solid @ink@; border-radius: 0; }
tooltip label { color: @ink@; font-family: "JetBrainsMono Nerd Font"; font-size: 12px; }
#custom-apps { padding: 0 12px 0 26px; border-right: 2px solid @ink@;
    background: @pink@; background-image: url("/home/marcos/.local/share/icons/Paperbit/16x16/actions/paperbit-heart.svg");
    background-repeat: no-repeat; background-position: 8px center; background-size: 16px 16px; }
#custom-terminal { padding: 0 10px; border-right: 1px solid @line@; }
#workspaces { padding: 0 6px; }
#workspaces .workspace-label { font-size: 18px; padding-right: 13px; }
#workspaces button.taskbar-window, #workspaces button.taskbar-window:hover {
    margin: 0; padding: 0 0 0 13px; border: 0; background: transparent; box-shadow: none; }
#workspaces .taskbar-window image { -gtk-icon-transform: translate(0px, -3px); }
#workspaces > button { padding: 0 4px; margin: 3px 2px; color: @muted@; background-color: transparent;
    background-position: center; background-repeat: no-repeat; background-size: 100% 24px;
    border: 1px solid transparent; box-shadow: none; }
#workspaces > button.active { color: @paper@; background-image: linear-gradient(@ink@, @ink@); }
#workspaces > button.urgent, #workspaces > button:hover {
    color: @ink@; background-image: linear-gradient(@pink@, @pink@); }
#clock { color: @ink@; padding: 0 14px;
    font-family: "JetBrainsMono Nerd Font", monospace; font-size: 14px;
    font-feature-settings: "zero=1"; }
#custom-clipboard { font-family: "Font Awesome 7 Free"; font-weight: 900; font-size: 14px;
    color: @rose@; padding: 0 10px; border-left: 1px dotted @line@; }
#custom-clipboard:hover { background: @pink@; color: @ink@; }
#pulseaudio, #network, #battery, #tray { padding: 0 10px; border-left: 1px dotted @line@; }
#custom-notifications { font-family: "Font Awesome 7 Free"; font-weight: 900; font-size: 14px;
    color: @ink@; padding: 0 10px; border-left: 1px dotted @line@; }
#custom-notifications.muted { color: @rose@; }
#custom-notifications:hover { background: @pink@; color: @ink@; }
#custom-session { padding: 0 10px; margin-left: 4px; border-left: 2px solid @ink@; }
#custom-terminal:hover, #custom-session:hover, #network:hover, #pulseaudio:hover { background: @pink@; }
#battery.warning { background: @pink@; color: @ink@; }
#battery.critical { background: @ink@; color: @paper@; }
#network.disconnected, #pulseaudio.muted { color: @muted@; }
''') + render((THEME/'spotify.css.in').read_text()))

write('.config/wofi/config','''width=480
height=380
show=drun
prompt=Buscar aplicaciones...
allow_images=true
image_size=24
insensitive=true
term=kitty
key_exit=Escape
''')
write('.config/wofi/style.css',render('''/* Paperbit · launcher y menú de sesión */
* { font-family: "JetBrainsMono Nerd Font", monospace; font-size: 13px; border-radius: 0; }
window { background: @paper@; color: @ink@; border: 2px solid @ink@; }
#outer-box { margin: 12px; }
#input { background: @surface@; color: @ink@; border: 2px solid @ink@;
    box-shadow: 3px 3px 0 @pink@; padding: 10px; margin: 0 3px 14px 0; }
#input:focus { border-color: @ink@; }
#input image { color: @ink@; }
#scroll { margin: 0; }
#entry { padding: 9px 10px; margin-bottom: 3px; border: 1px solid transparent; }
#entry:selected { background: @pink@; border: 1px solid @ink@; outline: none; }
#text { color: @ink@; margin: 0 6px; }
#text:selected { color: @ink@; }
#img { margin-right: 8px; }
'''))

kitty = (ROOT/'.config/kitty/kitty.conf').read_text()
if 'include paperbit.conf' not in kitty:
    kitty += '\n\n# Paperbit: colores; conserva fuente y tamaño personales.\ninclude paperbit.conf\n'
write('.config/kitty/kitty.conf',kitty)
write('.config/kitty/paperbit.conf',render('''# Paperbit · terminal en tinta, compatible con TUI de fondo oscuro
foreground @paper@
background @ink@
background_opacity 1.0
cursor @pink@
cursor_text_color @ink@
selection_foreground @ink@
selection_background @pink@
url_color @pink@
window_padding_width 10
tab_bar_style separator
tab_separator " │ "
active_tab_foreground @ink@
active_tab_background @pink@
inactive_tab_foreground @muted@
inactive_tab_background @surface@
tab_bar_background @ink@
# ANSI restringido a tinta/gris/rosa, con contraste sobre negro.
color0 @ink@
color1 #d49aaa
color2 #b8b8b8
color3 #c2aeb4
color4 #d0d0d0
color5 @pink@
color6 #ababab
color7 #e6e6e6
color8 @muted@
color9 @pink@
color10 #dedede
color11 #dbc3ca
color12 #efefef
color13 #f7dce3
color14 #c8c8c8
color15 @paper@
'''))

write('.config/mako/config',render('''font=JetBrainsMono Nerd Font 10
background-color=@paper@
text-color=@ink@
border-color=@ink@
border-size=2
border-radius=0
width=340
height=150
padding=14
margin=12
anchor=top-right
default-timeout=6000
max-visible=4
icons=1
icon-path=/home/marcos/.local/share/icons/Paperbit/16x16/apps
max-icon-size=32
progress-color=over @pink@

[urgency=critical]
background-color=@pink@
default-timeout=0

[mode=do-not-disturb]
invisible=1
'''))

write('.config/hypr/hyprlock.conf',render('''# Paperbit · pantalla de bloqueo
background {
    monitor =
    color = rgba(PAPERff)
}
input-field {
    monitor =
    size = 320, 52
    outline_thickness = 2
    rounding = 0
    outer_color = rgba(INKff)
    inner_color = rgba(PAPERff)
    font_color = rgba(INKff)
    check_color = rgba(PINKff)
    fail_color = rgba(ROSEff)
    font_family = JetBrainsMono Nerd Font
    placeholder_text = <i>Contraseña para desbloquear</i>
    fail_text = Inténtalo de nuevo
    fade_on_empty = false
    position = 0, -85
    halign = center
    valign = center
}
label {
    monitor =
    text = $TIME
    font_family = Classic Console
    font_size = 72
    color = rgba(INKff)
    position = 0, 60
    halign = center
    valign = center
}
label {
    monitor =
    text = [ SESIÓN BLOQUEADA ]
    font_family = Classic Console
    font_size = 14
    color = rgba(ROSEff)
    position = 0, -20
    halign = center
    valign = center
}
''').replace('PAPER',P['paper'][1:]).replace('PINK',P['pink'][1:]).replace('INK',P['ink'][1:]).replace('ROSE',P['rose'][1:]))

toolkit = {'background':'paper','base':'surface','text':'ink','alternate_base':'pink',
           'bright_text':'ink','accent':'rose','accent_secondary':'ink'}
write('.config/hypr/hyprtoolkit.conf', '\n'.join(f'{k} = 0xFF{P[v][1:]}' for k,v in toolkit.items()) + '''
font_family = Noto Sans
font_family_monospace = JetBrainsMono Nerd Font
icon_theme = Paperbit
rounding_large = 0
rounding_small = 0
''')

# KDE / Qt palette, preserving file associations and existing application settings.
scheme = cfg('/usr/share/color-schemes/BreezeLight.colors')
for section in scheme.sections():
    if section.startswith('Colors:'):
        for key in scheme[section]:
            role = ('pink' if section=='Colors:Selection' and key.startswith('Background')
                    else 'surface' if key=='BackgroundAlternate'
                    else 'paper' if key.startswith('Background')
                    else 'muted' if key=='ForegroundInactive'
                    else 'rose' if key in ('ForegroundLink','ForegroundVisited','ForegroundNegative')
                    else 'pink' if key=='DecorationHover'
                    else 'ink')
            scheme[section][key] = rgb(role)
set_cfg(scheme,'General',{'Name':'Paperbit','ColorScheme':'Paperbit'})
set_cfg(scheme,'WM',{'activeBackground':rgb('paper'),'activeForeground':rgb('ink'),
    'inactiveBackground':rgb('surface'),'inactiveForeground':rgb('muted'),
    'activeBlend':rgb('paper'),'inactiveBlend':rgb('surface')})
save_cfg('.local/share/color-schemes/Paperbit.colors',scheme)
kde = cfg(ROOT/'.config/kdeglobals')
for section in scheme.sections():
    if section.startswith('Colors:') or section.startswith('ColorEffects:') or section=='WM':
        set_cfg(kde,section,dict(scheme[section]))
set_cfg(kde,'General',{'ColorScheme':'Paperbit','Name':'Paperbit',
    'font':'Noto Sans,10,-1,5,50,0,0,0,0,0', 'fixed':'JetBrainsMono Nerd Font,10,-1,5,50,0,0,0,0,0'})
kde['General'].pop('ColorSchemeHash',None)
set_cfg(kde,'KDE',{'widgetStyle':'Windows','LookAndFeelPackage':'org.kde.breeze.desktop'})
set_cfg(kde,'Icons',{'Theme':'Paperbit'})
save_cfg('.config/kdeglobals',kde)

# GTK's Breeze variables; explicit CSS colors also reach GTK4/libadwaita apps.
oldcolors=(ROOT/'.config/gtk-3.0/colors.css').read_text()
gtkcolors=[]
for name in re.findall(r'@define-color\s+(\w+)\s+',oldcolors):
    role=('rose' if any(x in name for x in ['error','link','warning']) else
          'ink' if 'success' in name else
          'muted' if 'insensitive' in name and any(x in name for x in ['fg','text','foreground']) else
          'line' if 'border' in name else
          'ink' if any(x in name for x in ['fg','text','foreground']) else
          'pink' if 'selected' in name or 'hover' in name else
          'ink' if 'focus' in name or 'decoration' in name else 'paper')
    gtkcolors.append(f'@define-color {name} {P[role]};')
extra = {'theme_bg_color':'paper','theme_fg_color':'ink','theme_base_color':'paper','theme_text_color':'ink',
         'theme_selected_bg_color':'pink','theme_selected_fg_color':'ink','borders':'line',
         'accent_bg_color':'pink','accent_fg_color':'ink','accent_color':'rose',
         'window_bg_color':'paper','window_fg_color':'ink','view_bg_color':'paper','view_fg_color':'ink',
         'headerbar_bg_color':'surface','headerbar_fg_color':'ink','headerbar_border_color':'ink',
         'card_bg_color':'paper','card_fg_color':'ink','dialog_bg_color':'paper','dialog_fg_color':'ink',
         'popover_bg_color':'paper','popover_fg_color':'ink','sidebar_bg_color':'surface','sidebar_fg_color':'ink'}
gtkcolors += [f'@define-color {k} {P[v]};' for k,v in extra.items()]
for version in ('3.0','4.0'):
    base=f'.config/gtk-{version}'
    settings=cfg(ROOT/base/'settings.ini')
    set_cfg(settings,'Settings',{'gtk-application-prefer-dark-theme':'false','gtk-theme-name':'Breeze',
        'gtk-icon-theme-name':'Paperbit','gtk-font-name':'Noto Sans 10',
        'gtk-cursor-theme-name':'Breeze_Light','gtk-cursor-theme-size':'24'})
    save_cfg(base+'/settings.ini',settings)
    write(base+'/colors.css','\n'.join(gtkcolors)+'\n')
    style=render('''@import 'colors.css';
/* Paperbit: square controls; retain toolkit layouts and focus behavior. */
window, dialog { background-color: @paper@; color: @ink@; }
headerbar, toolbar { background-image: none; background-color: @surface@; color: @ink@;
    border-radius: 0; border-bottom: 1px solid @ink@; box-shadow: none; }
button, entry, searchentry, spinbutton, combobox, popover, menu, menuitem, notebook, tab {
    border-radius: 0; }
button { background-image: none; background-color: @surface@; color: @ink@; border-color: @line@; box-shadow: none; }
button:hover, button:checked, button.suggested-action { background-image: none; background-color: @pink@; color: @ink@; border-color: @ink@; }
entry, searchentry, textview, treeview, list, listview { background-color: @paper@; color: @ink@; }
entry:focus, searchentry:focus { border-color: @rose@; }
selection, row:selected, treeview:selected, flowboxchild:selected { background-color: @pink@; color: @ink@; }
scrollbar slider { border-radius: 0; background-color: @line@; min-width: 6px; min-height: 6px; }
progressbar progress, scale highlight { background-image: none; background-color: @rose@; border-radius: 0; }
tooltip { background-color: @ink@; color: @paper@; border-radius: 0; }
tooltip label { color: @paper@; }
''')
    if version == '4.0':
        # libadwaita >= 1.6 reads CSS variables instead of named GTK colors.
        variables={k.replace('_','-'):v for k,v in extra.items() if k.startswith(('accent_', 'window_', 'view_', 'headerbar_', 'card_', 'dialog_', 'popover_', 'sidebar_'))}
        style += '\n:root {\n' + '\n'.join(f'  --{k}: {P[v]};' for k,v in variables.items()) + '\n}\n'
    write(base+'/gtk.css',style)

# Original 16x16 pixel icons, with a complete Breeze fallback for other apps.
icons = {
 'folder': '<path d="M1 4h6l2 2h6v8H1z" fill="@paper@" stroke="@ink@"/><path d="M2 7h12v2H2z" fill="@pink@"/>',
 'terminal': '<path d="M1 2h14v12H1z" fill="@paper@" stroke="@ink@"/><path d="M2 3h12v2H2z" fill="@pink@"/><path d="M4 7l2 2-2 2m4 0h3" fill="none" stroke="@ink@"/>',
 'file': '<path d="M3 1h7l3 3v11H3z" fill="@paper@" stroke="@ink@"/><path d="M5 7h6M5 9h6M5 11h4" stroke="@ink@"/><path d="M10 1v4h3" fill="@pink@" stroke="@ink@"/>',
 'heart': '<path d="M2 3h4v2h4V3h4v5h-2v2h-2v2H8v2H6v-2H4v-2H2V8H0V5h2z" fill="@ink@"/><path d="M3 5h2v2h6V5h2v3h-2v2H9v2H7v-2H5V8H3z" fill="@pink@"/>',
 'home': '<path d="M1 7h2V5h2V3h2V1h2v2h2v2h2v2h2v2h-2v6H3V9H1z" fill="@ink@"/><path d="M4 8h8v6H4z" fill="@paper@"/><path d="M7 10h2v4H7z" fill="@pink@"/>',
 'trash': '<path d="M3 4h10v11H3z" fill="@paper@" stroke="@ink@"/><path d="M2 3h12M5 1h6M6 6v6M10 6v6" stroke="@ink@"/>',
 'browser':'<path d="M1 2h14v12H1z" fill="@paper@" stroke="@ink@"/><path d="M2 3h12v2H2z" fill="@pink@"/><path d="M4 7h8M4 9h6M4 11h8" stroke="@ink@"/>',
}
groups={'places':{'folder':'folder','folder-documents':'folder','folder-download':'folder',
 'folder-pictures':'folder','folder-music':'folder','folder-videos':'folder','folder-desktop':'folder',
 'user-home':'home','user-trash':'trash'},
 'apps':{'utilities-terminal':'terminal','kitty':'terminal','org.kde.konsole':'terminal',
 'system-file-manager':'folder','org.kde.dolphin':'folder','google-chrome':'browser','firefox':'browser'},
 'mimetypes':{'text-plain':'file','text-x-generic':'file','application-x-generic':'file'},
 'actions':{'paperbit-heart':'heart'}}
directories=[]
for group,names in groups.items():
    directories.append('16x16/'+group)
    for name,kind in names.items():
        svg=render('<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" shape-rendering="crispEdges">'+icons[kind]+'</svg>\n')
        write(f'.local/share/icons/Paperbit/16x16/{group}/{name}.svg',svg)
index='[Icon Theme]\nName=Paperbit\nComment=Original monochrome pixel icons with a pink accent\nInherits=breeze,hicolor\nDirectories='+','.join(directories)+'\n'
for directory in directories:
    context={'places':'Places','apps':'Applications','mimetypes':'MimeTypes','actions':'Actions'}[directory.split('/')[-1]]
    index+=f'\n[{directory}]\nSize=16\nType=Scalable\nMinSize=16\nMaxSize=128\nContext={context}\n'
write('.local/share/icons/Paperbit/index.theme',index)

keys={'color-scheme':'prefer-light','gtk-theme':'Breeze','icon-theme':'Paperbit',
      'cursor-theme':'Breeze_Light','font-name':'Noto Sans 10'}
old={key:subprocess.check_output(['gsettings','get','org.gnome.desktop.interface',key],text=True).strip() for key in keys}
(BACKUP/'gsettings.json').write_text(json.dumps(old,indent=2))
session='#!/bin/sh\n# Paperbit: preferencias que leen las aplicaciones GTK y los portales.\n'
for key,value in keys.items():
    session+=f'gsettings set org.gnome.desktop.interface {key} "{value}"\n'
write('.local/share/paperbit/session.sh',session)
(THEME/'last-backup').write_text(str(BACKUP)+'\n')
print('Paperbit generado. Copia de seguridad:', BACKUP)
