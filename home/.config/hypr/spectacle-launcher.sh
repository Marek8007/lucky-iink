#!/bin/sh
case "${XDG_CURRENT_DESKTOP:-}" in
    *Hyprland*) exec sh /home/marcos/.config/hypr/screenshot.sh "${1:-editor}" ;;
    *)
        case "${1:-}" in
            full) exec /usr/bin/spectacle -f ;;
            region) exec /usr/bin/spectacle -r ;;
            *) exec /usr/bin/spectacle "$@" ;;
        esac
        ;;
esac
