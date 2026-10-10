#!/usr/bin/env python3
"""Generate Himal OS branding assets for the Debian build.

Pure standard library - no Pillow, no ImageMagick. Writes PNGs directly.

  * himal-logo-{64,128,256,512}.png   the hex-badge mark
  * himal-wallpaper-{1920x1080,2560x1440}.png
  * himal-grub-background.png         (same as 1920x1080)

Credit: Build by Samir Puri
"""
import math
import pathlib
import struct
import zlib

# ---- brand palette (from the original Himal OS design) ----
NAVY_DARK = (0x07, 0x0E, 0x2A)
NAVY = (0x08, 0x14, 0x30)
BLUE = (0x12, 0x68, 0xA8)
SKY = (0x16, 0x98, 0xD2)
WHITE = (0xFF, 0xFF, 0xFF)

OUT_LOGO = pathlib.Path("config/includes.chroot/usr/share/pixmaps")
OUT_WALL = pathlib.Path("config/includes.chroot/usr/share/backgrounds/himal")

SS = 3  # supersampling factor for anti-aliasing


# ---------------------------------------------------------------- PNG writer
def write_png(path, w, h, rgb):
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += rgb[y * w * 3:(y + 1) * w * 3]

    def chunk(tag, data):
        c = tag + data
        return (struct.pack(">I", len(data)) + c
                + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF))

    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(bytes(raw), 6))
           + chunk(b"IEND", b""))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)
    return len(png)


# ---------------------------------------------------------------- geometry
def hex_points(cx, cy, r, rot_deg=0.0):
    """Flat-topped hexagon vertices (matches the Himal OS badge)."""
    pts = []
    for i in range(6):
        a = math.radians(rot_deg + 60 * i)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def point_in_poly(x, y, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xin = (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1
            if x < xin:
                inside = not inside
    return inside


def lerp(a, b, t):
    return a + (b - a) * t


def mix(c1, c2, t):
    return (int(lerp(c1[0], c2[0], t)),
            int(lerp(c1[1], c2[1], t)),
            int(lerp(c1[2], c2[2], t)))


# ---------------------------------------------------------------- the mark
def render_mark(size):
    """Hex badge: gradient fill, mountain silhouette, snow caps, moon."""
    W = H = size * SS
    buf = [(0, 0, 0)] * (W * H)

    cx, cy = W / 2, H / 2
    r = W * 0.46
    hexa = hex_points(cx, cy, r, rot_deg=90)   # pointy-top

    # inner hexagon (slightly smaller) for the "badge" look
    inner = hex_points(cx, cy, r * 0.86, rot_deg=90)

    # moon position (upper right inside the hexagon)
    mx, my, mr = cx + r * 0.42, cy - r * 0.40, r * 0.17

    # mountain ridge lines (fractions of the hexagon)
    big = [(-0.62, 0.30), (-0.10, -0.42), (0.30, 0.10), (0.30, 0.30)]
    small = [(0.10, 0.30), (0.38, -0.02), (0.66, 0.30)]

    for y in range(H):
        # vertical gradient across the whole badge
        t = y / (H - 1)
        grad = mix(SKY, NAVY_DARK, t)
        for x in range(W):
            if not point_in_poly(x + 0.5, y + 0.5, hexa):
                continue
            if not point_in_poly(x + 0.5, y + 0.5, inner):
                # thin border ring in sky blue
                buf[y * W + x] = SKY
                continue
            col = grad

            # moon
            if (x - mx) ** 2 + (y - my) ** 2 <= mr ** 2:
                col = WHITE

            # mountains: convert to absolute coords
            def to_abs(frac_pts):
                return [(cx + fx * r, cy + fy * r) for fx, fy in frac_pts]

            big_abs = to_abs(big)
            small_abs = to_abs(small)

            # fill below the ridge, above the hexagon's lower edge
            if point_in_poly(x + 0.5, y + 0.5, big_abs):
                col = NAVY_DARK
            elif point_in_poly(x + 0.5, y + 0.5, small_abs):
                col = NAVY

            buf[y * W + x] = col

    # downsample (box filter) for anti-aliasing
    out = bytearray()
    for y in range(size):
        for x in range(size):
            rs = gs = bs = 0
            for dy in range(SS):
                for dx in range(SS):
                    px = buf[(y * SS + dy) * W + (x * SS + dx)]
                    rs += px[0]; gs += px[1]; bs += px[2]
            n = SS * SS
            out += bytes((rs // n, gs // n, bs // n))
    return bytes(out)


# ---------------------------------------------------------------- wallpaper
def render_wallpaper(w, h):
    """Navy gradient with a large low-contrast badge watermark."""
    buf = bytearray()
    # diagonal gradient between NAVY_DARK and a slightly lighter navy/blue
    for y in range(h):
        for x in range(w):
            t = (x / (w - 1) * 0.45) + (y / (h - 1) * 0.55)
            buf += bytes(mix(NAVY, (0x0E, 0x2E, 0x52), t))

    # watermark: 256px mark scaled 2x, blended at 18% over the centre
    mark = render_mark(256)
    ms = 2
    mw = 256 * ms
    ox = (w - mw) // 2
    oy = (h - mw) // 2
    for y in range(mw):
        sy = y // ms
        for x in range(mw):
            sx = x // ms
            i = (sy * 256 + sx) * 3
            mr, mg, mb = mark[i], mark[i + 1], mark[i + 2]
            if mr == 0 and mg == 0 and mb == 0:
                continue
            j = ((oy + y) * w + (ox + x)) * 3
            a = 0.18
            buf[j] = int(buf[j] * (1 - a) + mr * a)
            buf[j + 1] = int(buf[j + 1] * (1 - a) + mg * a)
            buf[j + 2] = int(buf[j + 2] * (1 - a) + mb * a)
    return bytes(buf)


def main():
    for s in (64, 128, 256, 512):
        p = OUT_LOGO / f"himal-logo-{s}.png"
        n = write_png(p, s, s, render_mark(s))
        print(f"  {p}  ({s}x{s}, {n} bytes)")

    for (w, h) in ((1920, 1080), (2560, 1440)):
        p = OUT_WALL / f"himal-wallpaper-{w}x{h}.png"
        n = write_png(p, w, h, render_wallpaper(w, h))
        print(f"  {p}  ({w}x{h}, {n} bytes)")

    # grub background wants a plain name
    p = OUT_WALL / "himal-grub-background.png"
    if not p.exists():
        n = write_png(p, 1920, 1080, render_wallpaper(1920, 1080))
        print(f"  {p}  ({n} bytes)")


if __name__ == "__main__":
    main()
