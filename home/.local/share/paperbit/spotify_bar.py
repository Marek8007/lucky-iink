"""Spotify controls using Waybar's native MPRIS support; no playerctl CLI needed."""
def configure(bar):
    bar['modules-center'] = ['group/spotify']
    right = bar['modules-right']
    if 'clock' not in right:
        right.insert(0, 'clock')
    bar['group/spotify'] = {
        'orientation': 'horizontal',
        'modules': ['custom/spotify', 'mpris#previous', 'mpris#play', 'mpris#next', 'mpris#song'],
    }
    bar['custom/spotify'] = {
        'format': '\uf1bc', 'tooltip-format': 'Abrir Spotify',
        'on-click': 'gtk-launch com.spotify.Client',
    }
    call = ('gdbus call --session --dest org.mpris.MediaPlayer2.spotify '
            '--object-path /org/mpris/MediaPlayer2 --method org.mpris.MediaPlayer2.Player.')
    common = {'player': 'spotify', 'tooltip': True, 'hide-on-paused': False}
    bar['mpris#previous'] = dict(common, **{
        'format': '\uf048', 'tooltip-format': 'Canción anterior', 'on-click': call+'Previous',
    })
    bar['mpris#play'] = dict(common, **{
        'format': '{status_icon}',
        'status-icons': {'playing': '\uf04c', 'paused': '\uf04b', 'stopped': '\uf04b'},
        'tooltip-format': 'Reproducir / pausar',
    })
    bar['mpris#next'] = dict(common, **{
        'format': '\uf051', 'tooltip-format': 'Canción siguiente', 'on-click': call+'Next',
    })
    bar['mpris#song'] = dict(common, **{
        'format': '{dynamic}', 'dynamic-order': ['title', 'artist'],
        'dynamic-len': 28, 'title-len': 28, 'artist-len': 16, 'max-length': 28,
        'tooltip-format': '{title}\n{artist}\n{album}\nClic: reproducir/pausar · derecho: siguiente',
    })
