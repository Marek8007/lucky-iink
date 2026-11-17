#!/bin/sh
# Captura con el protocolo de Hyprland; Spectacle se usa como editor en XWayland.
runtime_dir=${XDG_RUNTIME_DIR:-/tmp}
state_dir=${XDG_STATE_HOME:-$HOME/.local/state}/paperbit
mkdir -p "$state_dir"
exec 2>"$state_dir/screenshot.log"
exec 9>"$runtime_dir/paperbit-screenshot-$(id -u).lock"
flock -n 9 || exit 0
notify() {
    gdbus call --session --dest org.freedesktop.Notifications \
        --object-path /org/freedesktop/Notifications \
        --method org.freedesktop.Notifications.Notify \
        'Paperbit' 0 'image-x-generic' "$1" "$2" '[]' '{}' 4000 >/dev/null 2>&1 || :
}
fail() {
    notify 'No se pudo capturar' 'Consulta ~/.local/state/paperbit/screenshot.log'
    exit 1
}
# Close the application menu before the selector takes keyboard focus.
sh /home/marcos/.config/hypr/app-menu.sh close
mode=${1:-region}
case "$mode" in
    region|editor)
        area=$(slurp -d -b '#17171766' -c '#efc7d1ff' -s '#ffffff00' -w 2 9>&-) || exit 0
        ;;
    full) area='' ;;
    *) exit 2 ;;
esac
pictures=$(xdg-user-dir PICTURES)
capture_dir="$pictures/Capturas de pantalla"
mkdir -p "$capture_dir" || fail
capture=$(mktemp "$capture_dir/Captura-$(date +%Y%m%d-%H%M%S)-XXXXXX.png") || fail
if [ -n "$area" ]; then
    grim -g "$area" "$capture" || fail
else
    grim "$capture" || fail
fi
wl-copy --type image/png < "$capture" 9>&- || exit 1
notify 'Captura copiada y guardada' 'Puedes pegarla con Ctrl+V o editarla en Spectacle.'
# This avoids Spectacle's KWin-only native Wayland capture backend.
setsid --fork env QT_QPA_PLATFORM=xcb /usr/bin/spectacle --new-instance --edit-existing "$capture" \
    9>&- </dev/null >>"$state_dir/spectacle-editor.log" 2>&1
