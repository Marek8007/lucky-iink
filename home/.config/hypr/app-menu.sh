#!/bin/sh
# Una sola instancia: otra pulsación cierra el lanzador existente.
if [ "${1:-}" = close ]; then
    pkill -u "$(id -u)" -x wofi 2>/dev/null || :
elif pgrep -u "$(id -u)" -x slurp >/dev/null; then
    # Releasing Win after Win+Shift+S must not steal the screenshot selector's focus.
    exit 0
elif pgrep -u "$(id -u)" -x wofi >/dev/null; then
    pkill -u "$(id -u)" -x wofi 2>/dev/null || :
else
    exec wofi --show drun
fi
