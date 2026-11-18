-- Configuración mínima para Hyprland 0.57.2 (Lua).
hl.monitor({ output = "", mode = "preferred", position = "auto", scale = "auto" })
-- Portátil abajo; monitor HDMI encima y centrado (coordenadas lógicas).
hl.monitor({ output = "eDP-1", mode = "preferred", position = "0x0", scale = 1 })
hl.monitor({ output = "HDMI-A-1", mode = "preferred", position = "0x-1080", scale = 1 })
hl.env("XCURSOR_SIZE", "24")
hl.env("HYPRCURSOR_SIZE", "24")

hl.config({
    input = {
        kb_layout = "es",
        follow_mouse = 1,
        touchpad = { natural_scroll = true, tap_to_click = true },
    },
    general = { layout = "dwindle" },
    dwindle = { preserve_split = true },
})

require("paperbit")

hl.on("hyprland.start", function()
    hl.exec_cmd("python3 /home/marcos/.local/share/paperbit/wallpaper.py")
    hl.exec_cmd("python3 /home/marcos/.local/share/paperbit/desktop_widgets.py")
    hl.exec_cmd("python3 /home/marcos/.local/share/paperbit/clipboard_history.py watch")
    hl.exec_cmd("sh /home/marcos/.local/share/paperbit/session.sh")
    hl.exec_cmd("waybar -c /home/marcos/.config/waybar/config.jsonc -s /home/marcos/.config/waybar/style.css")
    hl.exec_cmd("mako")
    hl.exec_cmd("/usr/libexec/polkit-kde-authentication-agent-1")
    -- Terminal disponible desde el primer momento, sin necesitar atajos.
    hl.exec_cmd("kitty")
end)

-- SUPER es la tecla Windows.
local function run(key, command)
    hl.bind(key, hl.dsp.exec_cmd(command))
end
run("SUPER + Return", "kitty")
run("CTRL + ALT + T", "kitty")
local appMenu = "sh /home/marcos/.config/hypr/app-menu.sh"
run("SUPER + D", appMenu)
run("SUPER + R", appMenu)
-- Abrir el menú al soltar Windows, también disponible con Win+D.
hl.bind("SUPER + Super_L", hl.dsp.exec_cmd(appMenu), { release = true, dont_inhibit = true })
-- Esc cierra todas las instancias y sigue funcionando dentro de las aplicaciones.
hl.bind("Escape", hl.dsp.exec_cmd(appMenu .. " close"), { non_consuming = true, dont_inhibit = true })
run("SUPER + E", "dolphin")
run("SUPER + N", "kitty --title 'Red y Wi-Fi' nmtui")
run("SUPER + ALT + T", "setsid --fork python3 /home/marcos/.local/share/paperbit/theme_switch.py toggle")
run("SUPER + L", "hyprlock")
run("SUPER + SHIFT + R", "hyprctl reload")
run("SUPER + SHIFT + E", "hyprctl dispatch 'hl.dsp.exit()'")
run("CTRL + ALT + Delete", "sh /home/marcos/.config/hypr/session-menu.sh")
-- Impr Pant, tecla dedicada de recorte y atajo habitual de teclados Windows.
for _, key in ipairs({ "Print", "XF86SelectiveScreenshot" }) do
    hl.bind(key, hl.dsp.exec_cmd("sh /home/marcos/.config/hypr/screenshot.sh"), { dont_inhibit = true, ignore_mods = true })
end
run("SUPER + SHIFT + S", "sh /home/marcos/.config/hypr/screenshot.sh")
hl.bind("SUPER + Q", hl.dsp.window.close())
hl.bind("ALT + F4", hl.dsp.window.close())
hl.bind("SUPER + V", hl.dsp.window.float({ action = "toggle" }))

for _, direction in ipairs({ "left", "right", "up", "down" }) do
    hl.bind("SUPER + " .. direction, hl.dsp.focus({ direction = direction }))
end
for workspace = 1, 10 do
    local key = workspace % 10
    hl.bind("SUPER + " .. key, hl.dsp.focus({ workspace = workspace }))
    hl.bind("SUPER + SHIFT + " .. key, hl.dsp.window.move({ workspace = workspace }))
end
hl.bind("SUPER + mouse:272", hl.dsp.window.drag(), { mouse = true })
hl.bind("SUPER + mouse:273", hl.dsp.window.resize(), { mouse = true })
run("XF86AudioRaiseVolume", "wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+")
run("XF86AudioLowerVolume", "wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-")
run("XF86AudioMute", "wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle")
-- Teclas multimedia: controlan Spotify incluso sin tener su ventana enfocada.
local spotifyCommand = "gdbus call --session --dest org.mpris.MediaPlayer2.spotify --object-path /org/mpris/MediaPlayer2 --method org.mpris.MediaPlayer2.Player."
for key, action in pairs({
    XF86AudioPlay = "PlayPause",
    XF86AudioPause = "Pause",
    XF86AudioPrev = "Previous",
    XF86AudioNext = "Next",
    XF86AudioStop = "Stop",
}) do
    hl.bind(key, hl.dsp.exec_cmd(spotifyCommand .. action), { locked = true, dont_inhibit = true })
end
run("XF86MonBrightnessUp", "brightnessctl set +5%")
run("XF86MonBrightnessDown", "brightnessctl set 5%-")
