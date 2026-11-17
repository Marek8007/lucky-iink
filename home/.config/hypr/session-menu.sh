#!/bin/sh
choice=$(printf '%s\n' 'Bloquear' 'Cerrar sesión' 'Reiniciar' 'Apagar' | wofi --dmenu --prompt 'Sesión' --width 350 --height 250) || exit 0
case "$choice" in
    'Bloquear') hyprlock ;;
    'Cerrar sesión') hyprctl dispatch 'hl.dsp.exit()' ;;
    'Reiniciar') systemctl reboot ;;
    'Apagar') systemctl poweroff ;;
esac
