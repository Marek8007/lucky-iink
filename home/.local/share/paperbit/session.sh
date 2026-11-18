#!/bin/sh
# Paperbit: preferencias que leen las aplicaciones GTK y los portales.
python3 /home/marcos/.local/share/paperbit/theme_switch.py --preferences
gsettings set org.gnome.desktop.interface gtk-theme "Breeze"
gsettings set org.gnome.desktop.interface icon-theme "Paperbit"
gsettings set org.gnome.desktop.interface cursor-theme "Breeze_Light"
gsettings set org.gnome.desktop.interface font-name "Noto Sans 10"
