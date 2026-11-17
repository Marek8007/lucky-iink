# Paperbit

Tema personal para Marcos, aplicado el 17 de noviembre de 2026 sobre Hyprland 0.57.2.
Blanco, tinta y rosa suave; tipografía e iconos de píxel en los controles del escritorio.

## Referencias y decisiones

Se consultó el [Top / All Time de r/unixporn](https://www.reddit.com/r/unixporn/top/?t=all)
y se contrastó con publicaciones populares de estética retro y monocroma.
La selección combina difusión y afinidad visual; no pretende medir toda la influencia
histórica del subreddit mediante una clasificación única.

| Referencia | Lectura de diseño y aplicación a Paperbit |
| --- | --- |
| [eDEX: A little project that I've been working on](https://www.reddit.com/r/unixporn/comments/9ysbx7/) | Una identidad visual que abarca toda una interfaz. En Paperbit se traduce en una paleta compartida por los componentes reales del escritorio. |
| [Hyprland: I <3 Quickshell](https://www.reddit.com/r/unixporn/comments/1l5ll27/) | Referencia destacada del listado Top para la futura integración de controles. Por ahora se conservan Waybar y sus funciones existentes; el módulo multimedia se reserva para la siguiente fase. |
| [Awesome: Afternoon In A Perfect World](https://www.reddit.com/r/unixporn/comments/hpakeu/) | El autor documenta un esquema de color propio y la personalización de terminal y cliente musical. La lección aplicada es coordinar las aplicaciones, además del fondo. |
| [LXQt: Another Simple Retro Theme](https://www.reddit.com/r/unixporn/comments/1ja6rsx/) | La combinación de fuentes Departure Mono / Classic Console, Chicago95 y Memphis98 sirve de referencia retro. Se reutiliza Classic Console, ya instalada, en la barra y el reloj del bloqueo. |
| [Sway: simple monochrome configuration](https://www.reddit.com/r/unixporn/comments/1oxozri/) | Paleta restringida y controles sobrios. Se aplica a superficies opacas, bordes rectos y rosa limitado a selecciones. |
| [KDE Plasma: Old Macintosh](https://www.reddit.com/r/unixporn/comments/1jsom9m/) | Fuente e iconografía como elementos de identidad. Paperbit añade iconos originales de 16 × 16 con trazos rectos y respaldo del conjunto Breeze. |

Los diseños anteriores son referencias: no se ejecutaron instaladores ni se copiaron
sus dotfiles. Los iconos de Paperbit están dibujados en SVG y no contienen ilustraciones
de Lukii Moi.

## Paleta

| Papel | Tinta | Superficie | Rosa | Rosa para texto |
| --- | --- | --- | --- | --- |
| `#ffffff` | `#171717` | `#f2f2f2` | `#efc7d1` | `#884258` |

Grises secundarios para bordes y texto desactivado. La terminal utiliza la versión
oscura de esta paleta para mantener legibles las aplicaciones TUI que usan sus propios
fondos oscuros. Sus colores ANSI se restringen a grises y rosas; las aplicaciones que
emiten colores RGB propios conservan esos colores.

## Alcance

- Hyprland: fondo blanco, márgenes, bordes rectos, opacidad completa y efectos sobrios.
- Waybar: barra en ambas pantallas, letra Classic Console, menú rosa e icono de píxel.
- Wofi: búsqueda y menú de sesión claros, selección rosa y sombra recta en el buscador.
- Kitty: fondo tinta, texto claro, selecciones y pestaña activa rosas. JetBrainsMono a 8 pt.
- Mako: notificaciones blancas con borde negro; urgentes rosas y persistentes.
- Hyprlock: reloj de píxel, campo rectangular y base blanca; visible en el próximo bloqueo.
- Hyprtoolkit: diálogos claros y sin redondeo.
- GTK3/GTK4: tema claro, controles cuadrados y colores coordinados.
- Qt/KDE: esquema Paperbit, estilo Windows y conjunto de iconos Paperbit con respaldo Breeze.
- Cursor Breeze Light.

La apariencia de aplicaciones ya abiertas puede requerir cerrarlas y abrirlas.
Los temas internos de navegadores, IDE, aplicaciones Electron, las páginas web y los
iconos proporcionados directamente por aplicaciones no siempre siguen la configuración
del escritorio. Los programas Flatpak también pueden necesitar configuración propia.
El gestor de acceso SDDM y la pantalla de arranque son independientes de este tema de usuario.

## Funcionalidad conservada

Se compararon los atajos y las reglas de monitores con la copia anterior: son idénticos.
También se conservaron todas las acciones de clic de la barra, los espacios de trabajo,
el acceso a red, volumen, batería, bandeja, bloqueo y menú de sesión.
El segundo monitor sigue encima del portátil. La fuente de Kitty sigue a 8 puntos.

## Personalizar y recargar

Los colores principales se editan en `~/.local/share/paperbit/palette.json`.
El generador produce los estilos y guarda una copia de cada archivo modificado:

```sh
python3 ~/.local/share/paperbit/apply.py
python3 ~/.local/share/paperbit/reload.py
```

La apariencia de Hyprland está en `~/.config/hypr/paperbit.lua`.
Los atajos, monitores y programas de inicio siguen en `~/.config/hypr/hyprland.lua`.
Editar directamente un estilo es posible; volver a ejecutar el generador sobrescribe
los archivos visuales que administra. Para cambios permanentes, ajustar el generador.

## Recuperar la configuración anterior

La ubicación de la copia original está en `~/.local/share/paperbit/original-backup`.
El manifiesto enumera cada archivo guardado y también registra cuáles eran nuevos.

```sh
python3 ~/.local/share/paperbit/restore.py
```

Después, volver a iniciar sesión para que todos los componentes usen la configuración
restaurada. La restauración recupera los archivos de antes de Paperbit; incluye los
archivos completos de Hyprland y Waybar guardados en esa fecha.

## Próximas fases acordadas

Fondo blanco con un cuadrado negro centrado de 320 × 320 píxeles lógicos en cada
monitor. El placeholder se dibuja en la capa de fondo mediante `wallpaper.py`,
sin interceptar ratón ni teclado. Tamaño y colores: `wallpaper.json`.
Se inicia automáticamente con Hyprland.
Carpeta preparada: `~/Pictures/Paperbit/illustrations/`.
Cuando lleguen las ilustraciones se decidirán tamaño, centrado e intervalo de rotación.
Spotify ya está integrado en el centro de la barra mediante MPRIS:
`SP` abre la aplicación; los tres botones permiten anterior, reproducir/pausar y siguiente.
El título muestra información de la canción y el tooltip incluye artista y álbum.
Con Spotify cerrado permanece `SP` y los controles se ocultan automáticamente.
El reloj está en la zona derecha. No requiere instalar el ejecutable playerctl.
La integración persiste al regenerar Paperbit mediante `spotify_bar.py` y `spotify.css.in`.

## Verificación

Hyprland valida sin errores y se ha recargado la sesión activa. Waybar se ha comprobado
en las dos pantallas; corregido y verificado el formato de reloj. Los parsers GTK3 y GTK4
aceptan los estilos. Kitty carga los colores y conserva 8 pt. Mako acepta la recarga.
Wofi se ha abierto y revisado mediante captura, sin errores. Se ha comprobado el arranque
de un diálogo Qt. Hyprlock no se ha activado como prueba para evitar bloquear la sesión
durante el trabajo; su apariencia se comprobará en el próximo bloqueo normal.

## Ventanas fijas del escritorio

En ambas pantallas, `desktop_widgets.py` dibuja tres paneles en la capa inferior
del escritorio: fastfetch a la izquierda, btop arriba a la derecha y Spotify
con espectro CAVA abajo a la derecha. No toman el foco ni reservan espacio:
las aplicaciones los cubren y aparecen en todos los espacios de trabajo.
El centro queda disponible para la ilustración. Se inician con Hyprland.

El visualizador captura exclusivamente el flujo de salida de Spotify mediante
`parec --monitor-stream` y CAVA; no utiliza el micrófono. Se detiene si Spotify
está pausado o cerrado. El análisis es compartido entre ambas pantallas.
Los datos de canción, artista y progreso se leen mediante MPRIS.

Btop muestra CPU, memoria y procesos ordenados por memoria de mayor a menor, con
configuración propia en `widgets/btop.conf` y tema Paperbit. La configuración
del btop que abres manualmente se conserva.

Herramientas instaladas: fastfetch, cava y VTE (terminal GTK embebida).
Diagnóstico: `~/.local/state/paperbit/widgets.log`.

El fetch es más alto y está desplazado hacia arriba. Spotify ocupa una franja
horizontal bajo la imagen central, con 24 píxeles de separación; btop se extiende
desde la parte superior derecha hasta esa franja. Las medidas se adaptan a cada monitor.

## Personalizar el fetch

La información la genera Fastfetch, configurado en `~/.config/fastfetch/paperbit.json`.
La imagen se configura aparte en `~/.local/share/paperbit/fetch.json`:
`image` es la ruta, `image_height` el alto máximo y `pixel_art` activa escalado
sin suavizado. Por defecto muestra el corazón de Paperbit a 96 píxeles lógicos
de alto máximo, conservando las proporciones. Admite imágenes cargables por GdkPixbuf,
como PNG, JPEG y SVG. El tamaño de la ventana no cambia al cambiar de imagen.

Los datos son una instantánea al iniciar el panel, mientras btop sí se actualiza
en directo. Los cambios de imagen o campos se aplican reiniciando los paneles.

## Tiempo y altura del fetch

El fetch ajusta su altura al texto y la imagen cuando termina Fastfetch, con
márgenes mínimos. El cuarto panel, Tiempo de Valencia, queda a la izquierda, centrado con el
fetch y a la altura del hueco entre btop y Spotify, en ambas pantallas. Temperatura, sensación, cielo, viento
y máxima/mínima: Open-Meteo (https://open-meteo.com/). Se actualiza cada 15 minutos
en segundo plano. Si falla la red conserva la última lectura y muestra que
está sin actualizar. Ubicación y frecuencia: `weather.json`.

El tiempo ocupa 320 × 112 píxeles lógicos, con tipografía JetBrainsMono y
cabecera Classic Console. Un dibujo ASCII cambia según el código meteorológico:
sol, intervalos nubosos, nubes, lluvia, tormenta, nieve o niebla. Btop ajusta su
altura para dejar 16 píxeles de separación encima y debajo del panel del tiempo.

El ASCII meteorológico combina colores de texto y de fondo en blanco, negro,
gris y rosa. En la pantalla del portátil la ilustración del fetch se compacta
cuando hace falta para evitar solaparse con el tiempo, conservando todos los datos.

## Rotación de ilustraciones Lukii Moi

Se sustituyó el placeholder por las imágenes de `~/Imágenes/lukii/` (42 al configurarlo).
El fondo sigue blanco; cada imagen encaja en un área de 320 × 320, centrada y sin
recorte ni deformación. Las dos pantallas muestran la misma imagen.
La colección rota cada 300 segundos con selección aleatoria independiente;
puede repetirse cualquier imagen, incluida la que se está mostrando. Los originales se conservan intactos y la carpeta se vuelve
a consultar en cada cambio para reconocer imágenes nuevas.

Ajustes en `~/.local/share/paperbit/wallpaper.json`: `size`, `image_directory`,
`rotation_seconds` y `shuffle`. Se conserva la selección y la cola al reiniciar.
Para aplicar ajustes, enviar SIGUSR1 al proceso `wallpaper.py`; para pasar
a la siguiente imagen, SIGUSR2. El registro está en
`~/.local/state/paperbit/wallpaper.log`. Se comprobó la decodificación de las
42 imágenes y el cambio de imagen en la sesión activa.

Un clic izquierdo sobre la ilustración pasa a la siguiente imagen en ambas
pantallas. La rotación automática de cinco minutos continúa activa. Solo el
área de la ilustración recibe clics; el resto del fondo deja pasar el ratón.

## Capturas en Hyprland

Impr Pant, la tecla dedicada de recorte y Win+Mayús+S seleccionan una región
con slurp y la capturan con grim. Se guarda en `~/Imágenes/Capturas de pantalla/`,
se copia como PNG al portapapeles y se abre en Spectacle para editar o anotar.
Esc cancela la selección. El bloqueo de instancia se libera mientras editas,
para poder realizar nuevas capturas. El menú de Windows no roba el foco de slurp.

Esta versión de Spectacle requiere KWin para capturar de forma nativa en Wayland.
Por eso se utiliza como editor mediante XWayland, con la imagen real capturada
previamente por grim. Para otra captura, usar de nuevo la tecla o el lanzador,
en lugar de la captura nativa de la ventana del editor.
El lanzador local de Spectacle usa este flujo en Hyprland; en KDE ejecuta
Spectacle de la forma habitual. Incluye una acción para capturar todo el escritorio.

Diagnóstico: `~/.local/state/paperbit/screenshot.log` y `spectacle-editor.log`.

## Lluvia de píxeles

El fondo dibuja cuadrados negros de 2–4 píxeles que caen con posición y velocidad
aleatorias. Se renderizan en la capa de fondo, detrás de aplicaciones y paneles;
la ilustración conserva el clic para cambiar de imagen. El efecto funciona en
ambas pantallas y se inicia junto al fondo.

Configuración en `wallpaper.json`, sección `rain`: `enabled`, `count` (densidad
por pantalla Full HD), `fps`, `min_speed`, `max_speed` y `sizes`. Valor inicial:
90 partículas por pantalla, 30 fps y velocidades de 35–95 píxeles por segundo.
Para desactivarlo, poner `enabled` a `false` y recargar el fondo con SIGUSR1.

`allow_repeats: true` elige entre todas las imágenes en cada clic o cambio
automático, permitiendo repeticiones.
