-- Paperbit: aspecto visual. Funciones y monitores en hyprland.lua.
hl.env("QT_QPA_PLATFORMTHEME", "kde")
hl.env("QT_STYLE_OVERRIDE", "Windows")
hl.env("XCURSOR_THEME", "Breeze_Light")
hl.config({
    general = {
        gaps_in = 5, gaps_out = 12, border_size = 2,
        col = { active_border = "rgba(171717ff)", inactive_border = "rgba(b8b8b8ff)" },
    },
    decoration = {
        rounding = 0, active_opacity = 1.0, inactive_opacity = 1.0,
        blur = { enabled = false }, shadow = { enabled = false },
    },
    animations = { enabled = false },
    misc = {
        disable_hyprland_logo = true, disable_splash_rendering = true,
        background_color = "rgba(ffffffff)",
    },
})
