"""Shared light/dark colors and view-only illustration conversion for Paperbit."""
import json
from pathlib import Path
import re

ROOT=Path.home()/'.local/share/paperbit'
try: DARK=json.loads((ROOT/'theme.json').read_text()).get('mode')=='dark'
except (OSError,ValueError): DARK=False

DARK_COLORS={
    '#ffffff':'#171717','#171717':'#ffffff','#000000':'#ffffff',
    '#f2f2f2':'#242424','#626262':'#b8b8b8','#b8b8b8':'#555555',
    '#efc7d1':'#6e3f50','#884258':'#e7a6bd','#a34f70':'#e7a6bd',
    '#f8e3ea':'#3d2932','#e49ab5':'#88425e',
    '#aaaaaa':'#777777','#404040':'#d0d0d0','#444444':'#d8d8d8',
    '#66545a':'#d1a9b7','#f5f5f5':'#202020',
    '#b7788c':'#b7788c','#a05c73':'#c58ca1','#78394e':'#e4a4ba',
    '#ad6982':'#d28da7','#a77386':'#c68ca2',
}
def resolve_color(value,dark=None):
    active=DARK if dark is None else dark
    return DARK_COLORS.get(value.lower(),value) if active else value

def tint(text,dark=None):
    active=DARK if dark is None else dark
    if not active:return text
    return re.sub(r'#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?\b',
        lambda m:resolve_color(m[0][:7],True)+m[0][7:],text)

def tint_bytes(data):return tint(data.decode()).encode()

def rgb(value):
    value=resolve_color(value)
    return tuple(int(value[i:i+2],16)/255 for i in (1,3,5))

def image_theme(pixbuf):
    """Invert only neutral pixels in memory, leaving saturated pink and alpha intact."""
    if not DARK:return pixbuf
    from gi.repository import GdkPixbuf,GLib
    data=bytearray(pixbuf.get_pixels())
    channels=pixbuf.get_n_channels();stride=pixbuf.get_rowstride()
    for y in range(pixbuf.get_height()):
        for x in range(pixbuf.get_width()):
            offset=y*stride+x*channels
            r,g,b=data[offset:offset+3]
            if max(r,g,b)-min(r,g,b)<24:
                for i in range(3):data[offset+i]=23+round((255-data[offset+i])*232/255)
    return GdkPixbuf.Pixbuf.new_from_bytes(GLib.Bytes.new(bytes(data)),
        GdkPixbuf.Colorspace.RGB,pixbuf.get_has_alpha(),8,
        pixbuf.get_width(),pixbuf.get_height(),stride)
