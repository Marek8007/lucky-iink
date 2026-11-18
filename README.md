# lucky-iink / Paperbit

Escritorio personal para **Hyprland 0.57.2 en openSUSE Tumbleweed**: blanco y negro,
acentos rosas, controles retro y detalles de píxel. Todos los archivos de configuración
se mantienen en `home/`; el instalador crea enlaces desde sus rutas habituales.

## Qué incluye

- Dos pantallas Full HD al 100 %, con HDMI encima del portátil.
- Waybar con Spotify, reproducción/anterior/siguiente, reloj con segundos, red,
  volumen, batería, bandeja y menú de sesión.
  Al pulsar la fecha abre un calendario desplegable bajo la barra. Se cierra
  con Esc, pulsando fuera o repitiendo el clic; incluye navegación por meses y Hoy.
  Las semanas empiezan en lunes: lunes–jueves blancos, viernes rosa claro y
  sábado–domingo rosa intenso. El día seleccionado se distingue con un borde negro.
- Paneles fijos detrás de las aplicaciones y visibles en todos los escritorios:
  Fastfetch, btop con procesos por memoria y actualización a 500 ms, visualizador
  CAVA del audio real de Spotify y tiempo de Valencia con ASCII de colores.
  Esperan a que cada monitor comunique sus dimensiones y se recolocan al cambiar
  la resolución, la escala o al volver a conectar una pantalla.
- Ilustraciones centradas, cambio con clic y selección aleatoria cada cinco
  minutos, con repeticiones permitidas. Lluvia de píxeles negros en el fondo.
- Kitty a 12 puntos, Wofi, Mako, Hyprlock, tema GTK/Qt y pequeños iconos propios.
- Recortes con grim/slurp, copia al portapapeles, guardado y edición con Spectacle.

## Mapa de archivos

| Configuración | Ruta dentro de `home/` |
| --- | --- |
| Atajos, pantallas y arranque | `.config/hypr/hyprland.lua` |
| Apariencia de Hyprland | `.config/hypr/paperbit.lua` |
| Barra y estilos | `.config/waybar/` |
| Terminal | `.config/kitty/` |
| Menú y notificaciones | `.config/wofi/`, `.config/mako/` |
| Campos de Fastfetch | `.config/fastfetch/paperbit.json` |
| Imagen del fetch | `.local/share/paperbit/fetch.json` |
| Tamaños y posición de paneles | `.local/share/paperbit/desktop_widgets.py` |
| Inicialización y cambios de monitor | `.local/share/paperbit/monitor_layout.py` |
| Ciudad del tiempo | `.local/share/paperbit/weather.json` |
| Imágenes, intervalo y lluvia | `.local/share/paperbit/wallpaper.json` |
| Btop del escritorio y sus colores | `.local/share/paperbit/widgets/` |
| Btop que se abre manualmente | `.config/btop/btop.conf` |
| Ilustraciones | `Imágenes/lukii/` |

## Instalar

La instalación enlaza los archivos y guarda los anteriores en
`~/.local/state/lucky-iink/backups/`. No instala paquetes ni cambia de sesión.

```sh
git clone https://github.com/Marek8007/lucky-iink.git
cd lucky-iink
python3 scripts/install.py --dry-run
python3 scripts/install.py
```

Conserva esta carpeta en su ubicación: los enlaces apuntan a ella. En otro usuario,
el instalador adapta las rutas de la cuenta original en `.generated/`, dentro del
proyecto. Los nombres de monitor, la distribución, la fuente disponible y la ciudad
deben ajustarse para cada equipo. Es una configuración personal, no una distribución.

Dependencias principales para openSUSE:

```sh
sudo zypper install hyprland hyprland-guiutils kitty waybar wofi mako hyprlock \
  grim slurp wl-clipboard spectacle fastfetch btop cava typelib-1_0-Vte-2_91 \
  libgtk-layer-shell0 python3-gobject python3-cairo
```

También necesita PipeWire/PulseAudio (`pactl`, `parec`, `wpctl`), GTK3, GdkPixbuf,
Python 3 y las utilidades habituales de util-linux. Usa las fuentes **Classic Console**,
**JetBrainsMono Nerd Font**, **Noto Sans** y **Font Awesome 7**. Las fuentes y los
paquetes del sistema no se distribuyen dentro de este repositorio. El tema Qt utiliza
el complemento de KDE y el estilo Windows; los iconos recurren a Breeze cuando falta
un icono propio. El agente Polkit tiene la ruta de openSUSE.

Para aplicar el tema claro a las preferencias GTK/portales:

```sh
sh ~/.local/share/paperbit/session.sh
```

Después, entrar en Hyprland o recargar los componentes. El funcionamiento actual
se ha comprobado en el equipo original con dos pantallas 1920 × 1080.

## Cambiar y recargar

### Claro y oscuro

Pulsa **[ tema ]** en la barra o **Win+Alt+T** para alternar sin cerrar sesión.
El modo elegido se conserva al reiniciar. También puedes elegirlo explícitamente:

```sh
python3 ~/.local/share/paperbit/theme_switch.py light
python3 ~/.local/share/paperbit/theme_switch.py dark
```

La variante oscura invierte papel/tinta y adapta los grises y rosas para mantener
el contraste. Incluye paneles, calendario, lluvia, barra, menús, GTK/Qt, notificaciones
y bloqueo. Kitty conserva su fondo oscuro en ambos modos para respetar los colores
propios de las aplicaciones TUI. Las aplicaciones abiertas con temas internos
pueden necesitar reabrirse o seleccionar su opción de seguir el tema del sistema.

Las ilustraciones invierten solo sus tonos neutros en memoria; los rosas se
mantienen y los originales no se modifican. El perfil claro se guarda en
`home/.local/share/paperbit/themes/light/files/`; el oscuro se deriva mediante
`theme_support.py`. Para personalizaciones que sobrevivan a la alternancia, editar
el perfil claro o el mapa de colores oscuro, y aplicar el modo de nuevo. Los atajos,
monitores, tamaños y controles se conservan. `theme.json` contiene la elección actual.

Los enlaces permiten editar tanto el archivo de `~/.config/` como el de `home/`:
ambos apuntan al mismo contenido del repositorio.

```sh
hyprctl reload
python3 ~/.local/share/paperbit/reload.py
```

La segunda orden reinicia Waybar y recarga Kitty/Mako. Los paneles de escritorio
y el fondo son procesos independientes. Para recargar las opciones del fondo:

```sh
pkill -USR1 -f '^python3 /home/.*/.local/share/paperbit/wallpaper.py$'
```

Los cambios de código o geometría de los paneles requieren reiniciar
`desktop_widgets.py` o volver a entrar en la sesión. `apply.py` es el generador
inicial de estilos: **no es el instalador del repositorio** y puede sobrescribir
personalizaciones visuales realizadas después.

## Restaurar

```sh
python3 scripts/restore.py
```

Recupera la copia anterior a la última instalación, sin sobrescribir archivos que
hayan dejado de ser los enlaces instalados. También acepta la ruta de una copia
concreta. Recarga la sesión después. Las copias, cachés y registros permanecen fuera
del repositorio; las capturas de pantalla tampoco se incluyen.

## Atajos principales

| Atajo | Acción |
| --- | --- |
| Win / Win+D | Abrir/cerrar aplicaciones; Esc también cierra |
| Win+Enter / Ctrl+Alt+T | Kitty |
| Win+E | Archivos |
| Win+N | Red y Wi-Fi |
| Win+Q / Alt+F4 | Cerrar ventana |
| Win+V | Alternar flotante |
| Win+arrastrar, izquierdo/derecho | Mover/redimensionar |
| Win+flechas | Cambiar foco |
| Win+1–9/0 | Escritorio 1–10 |
| Win+Mayús+1–9/0 | Mover ventana al escritorio |
| Impr Pant / tecla de recorte / Win+Mayús+S | Capturar área |
| Win+L | Bloqueo |
| Ctrl+Alt+Supr | Menú de sesión |
| Teclas multimedia | Controlar Spotify |

Spectacle no captura nativamente en Hyprland con esta versión: el lanzador usa
grim/slurp y abre el resultado en su editor mediante XWayland. Para otra captura,
usar de nuevo el atajo o el lanzador. En KDE, el lanzador ejecuta Spectacle normalmente.

## Créditos

Las ilustraciones de `home/Imágenes/lukii/` son de **Lukii Moi**, aportadas para este
escritorio. No son obra del autor de esta configuración y no se les concede una
licencia nueva desde este repositorio. Se conservan sus archivos originales.
El tema de btop parte de Adwaita, de flipflop133; conserva sus créditos.
Los datos meteorológicos proceden de [Open-Meteo](https://open-meteo.com/).
Las aplicaciones y fuentes pertenecen a sus respectivos autores.

Las referencias de r/unixporn y notas detalladas están en
[docs/CONFIGURATION.md](docs/CONFIGURATION.md). Esas notas también recogen fases
anteriores del diseño; este README describe la organización actual del repositorio.
