#!/bin/sh
set -eu

if [ "${1:-}" = toggle ]; then
    makoctl mode -t do-not-disturb
    pkill -RTMIN+4 -u "$(id -u)" -x waybar
    exit
fi

modes=$(makoctl mode)
if printf '%s\n' "$modes" | grep -Fxq do-not-disturb; then
    printf '%s\n' '{"text":"","class":"muted","tooltip":"No molestar activado · Clic para volver a mostrar avisos"}'
else
    printf '%s\n' '{"text":"","class":"unmuted","tooltip":"Notificaciones activas · Clic para silenciarlas"}'
fi
