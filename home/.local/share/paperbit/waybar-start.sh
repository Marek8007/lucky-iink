#!/bin/sh
set -eu
module=${XDG_DATA_HOME:-"$HOME/.local/share"}/paperbit/waybar/workspaces.so
if [ -r "$module" ]; then
    GTK_MODULES="$module${GTK_MODULES:+:$GTK_MODULES}"
    export GTK_MODULES
fi
config=${XDG_CONFIG_HOME:-"$HOME/.config"}/waybar
exec waybar -c "$config/config.jsonc" -s "$config/style.css"
