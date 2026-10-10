#!/usr/bin/env python3
"""Himal OS boot splash + desktop art.

Builds a Windows-style Plymouth splash: dark background, the Himal OS badge
centred, the wordmark beneath it, "Build by Samir Puri" under that, and the
Windows-style ring of dots that rotate around the logo while the system boots.

Also emits the logo used by the login greeter and three Himal wallpapers.

Credit: Build by Samir Puri
"""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from make_assets import render_mark, write_png  # noqa: E402

THEME_DIR = pathlib.Path("config/includes.chroot/usr/share/plymouth/themes/himal")
PIXMAPS = pathlib.Path("config/includes.chroot/usr/share/pixmaps")
BG_DIR = pathlib.Path("config/includes.chroot/usr/share/backgrounds/himal")

# Windows-style palette: near-black navy, not pure black
BG_TOP = (0x05, 0x0A, 0x1C)
BG_BOTTOM = (0x08, 0x14, 0x30)

N_DOTS = 8
RADIUS = 46
DOT_R = 5


def plymouth_script():
    """Emit the Plymouth script.

    Trig is avoided deliberately: Plymouth's Math library is poorly specified, so
    the dot ring's coordinates are precomputed here and emitted as literals. The
    rotation is a stepped phase with fully unrolled opacity assignments, which
    keeps the script to constructs that are certain to work.
    """
    cx_expr = "Window.GetWidth() / 2"
    cy_expr = "Window.GetHeight() / 2 - 40"

    out = []
    out.append("# Himal OS boot splash - Windows-style centred logo with a rotating dot ring.")
    out.append("# Build by Samir Puri")
    out.append("")
    out.append(f"Window.SetBackgroundTopColor({BG_TOP[0]/255:.3f}, {BG_TOP[1]/255:.3f}, {BG_TOP[2]/255:.3f});")
    out.append(f"Window.SetBackgroundBottomColor({BG_BOTTOM[0]/255:.3f}, {BG_BOTTOM[1]/255:.3f}, {BG_BOTTOM[2]/255:.3f});")
    out.append("")
    out.append("cx = " + cx_expr + ";")
    out.append("cy = " + cy_expr + ";")
    out.append("")
    # --- logo, centred
    out.append('logo_image = Image("logo.png");')
    out.append("logo_image = logo_image.Scale(150, 150);")
    out.append("logo_sprite = Sprite(logo_image);")
    out.append("logo_sprite.SetX(cx - 75);")
    out.append("logo_sprite.SetY(cy - 105);")
    out.append("")
    # --- wordmark + credit
    out.append('title_image = Image.Text("Himal OS", 1, 1, 1, 1);')
    out.append("title_sprite = Sprite(title_image);")
    out.append("title_sprite.SetX(cx - title_image.GetWidth() / 2);")
    out.append("title_sprite.SetY(cy + 62);")
    out.append('credit_image = Image.Text("Build by Samir Puri", 0.55, 0.75, 0.90, 1);')
    out.append("credit_sprite = Sprite(credit_image);")
    out.append("credit_sprite.SetX(cx - credit_image.GetWidth() / 2);")
    out.append("credit_sprite.SetY(cy + 62 + title_image.GetHeight() + 8);")
    out.append("")
    # --- the rotating dot ring
    for i in range(N_DOTS):
        ang = math.radians(90 - i * (360.0 / N_DOTS))
        dx = round(RADIUS * math.cos(ang), 3)
        dy = round(-RADIUS * math.sin(ang), 3)
        out.append(f'dot{i}_image = Image("dot.png");')
        out.append(f"dot{i}_sprite = Sprite(dot{i}_image);")
        out.append(f"dot{i}_sprite.SetX(cx + {dx} - {DOT_R});")
        out.append(f"dot{i}_sprite.SetY(cy + {dy} - {DOT_R});")
        out.append(f"dot{i}_sprite.SetOpacity(0.25);")
    out.append("")
    # --- phase stepping, fully unrolled so no array or modulo support is needed
    out.append("phase = 0;")
    out.append("Refresh() {")
    out.append("    phase = phase + 1;")
    out.append(f"    if (phase >= {N_DOTS}) phase = phase - {N_DOTS};")
    for lead in range(N_DOTS):
        out.append(f"    if (phase == {lead}) {{")
        for i in range(N_DOTS):
            trail = (lead - i) % N_DOTS          # 0 = leading dot
            opacity = max(0.18, 1.0 - trail * 0.105)
            out.append(f"        dot{i}_sprite.SetOpacity({opacity:.3f});")
        out.append("    }")
    out.append("}")
    out.append("Plymouth.SetRefreshFunction(Refresh);")
    out.append("")
    return "\n".join(out)


PLYMOUTH_CONF = """\
[Plymouth Theme]
Name=Himal OS
Description=Himal OS boot splash - Windows-style
ModuleName=script

[script]
ImageDir=/usr/share/plymouth/themes/himal
ScriptFile=/usr/share/plymouth/themes/himal/himal.script
"""


def dot_png():
    """A soft white dot with an alpha-free edge (Plymouth handles opacity)."""
    r = DOT_R
    size = r * 2
    px = bytearray()
    for y in range(size):
        for x in range(size):
            dx, dy = x - r + 0.5, y - r + 0.5
            d = math.hypot(dx, dy)
            if d <= r - 1:
                px += bytes((255, 255, 255))
            elif d <= r:
                # soft edge
                t = (r - d)
                v = int(255 * t)
                px += bytes((v, v, v))
            else:
                px += bytes((0, 0, 0))
    return size, size, bytes(px)


def gradient_wallpaper(w, h, top, bottom, badge_alpha=0.18):
    """Vertical gradient with the badge watermark, in an arbitrary palette."""
    buf = bytearray()
    for y in range(h):
        t = y / (h - 1)
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        row = bytes((r, g, b)) * w
        buf += row

    mark = render_mark(256)
    scale = 2
    mw = 256 * scale
    ox, oy = (w - mw) // 2, (h - mw) // 2
    for y in range(mw):
        sy = y // scale
        for x in range(mw):
            sx = x // scale
            i = (sy * 256 + sx) * 3
            mr, mg, mb = mark[i], mark[i + 1], mark[i + 2]
            if mr == 0 and mg == 0 and mb == 0:
                continue
            j = ((oy + y) * w + (ox + x)) * 3
            a = badge_alpha
            buf[j] = int(buf[j] * (1 - a) + mr * a)
            buf[j + 1] = int(buf[j + 1] * (1 - a) + mg * a)
            buf[j + 2] = int(buf[j + 2] * (1 - a) + mb * a)
    return bytes(buf)


WALLPAPERS = {
    # name: (top, bottom, badge alpha)
    "himal-wallpaper-abyss":  ((0x03, 0x06, 0x14), (0x0A, 0x1E, 0x3C), 0.20),
    "himal-wallpaper-dusk":   ((0x0B, 0x0A, 0x24), (0x24, 0x18, 0x46), 0.20),
    "himal-wallpaper-ice":    ((0xE8, 0xF2, 0xFA), (0xB9, 0xD4, 0xEA), 0.30),
    "himal-wallpaper-ember":  ((0x14, 0x06, 0x0A), (0x3A, 0x14, 0x1E), 0.20),
}


def main():
    print("--- Plymouth splash theme ---")
    THEME_DIR.mkdir(parents=True, exist_ok=True)
    (THEME_DIR / "himal.plymouth").write_text(PLYMOUTH_CONF, encoding="utf-8")
    print(f"  {THEME_DIR}/himal.plymouth")
    (THEME_DIR / "himal.script").write_text(plymouth_script(), encoding="utf-8")
    n = len(plymouth_script().splitlines())
    print(f"  {THEME_DIR}/himal.script ({n} lines)")

    # logo for the splash (and the greeter)
    write_png(THEME_DIR / "logo.png", 256, 256, render_mark(256))
    print(f"  {THEME_DIR}/logo.png")

    w, h, px = dot_png()
    write_png(THEME_DIR / "dot.png", w, h, px)
    print(f"  {THEME_DIR}/dot.png")

    PIXMAPS.mkdir(parents=True, exist_ok=True)
    write_png(PIXMAPS / "himal-logo-greeter.png", 256, 256, render_mark(256))
    print(f"  {PIXMAPS}/himal-logo-greeter.png")

    print("--- wallpapers ---")
    BG_DIR.mkdir(parents=True, exist_ok=True)
    for name, (top, bottom, alpha) in WALLPAPERS.items():
        p = BG_DIR / f"{name}.png"
        write_png(p, 2560, 1440, gradient_wallpaper(2560, 1440, top, bottom, alpha))
        print(f"  {p}")


if __name__ == "__main__":
    main()
