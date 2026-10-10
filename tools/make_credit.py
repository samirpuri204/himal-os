#!/usr/bin/env python3
"""Himal OS developer credit — desktop and home, made persistent.

Four layers, strongest first:

  1. Baked into the wallpaper image itself. Cannot be removed without replacing
     the artwork, and reads as part of the design rather than a sticker.
  2. A desktop icon that opens the About window.
  3. A file in the home directory, owned by root, mode 444, chattr +i.
  4. A self-healing systemd timer that restores (3) from a root-owned master copy
     if it is deleted or edited.

Credit: Build by Samir Puri
"""
import os
import pathlib
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from make_splash import WALLPAPERS, gradient_wallpaper  # noqa: E402

ROOT = pathlib.Path("config/includes.chroot")
BG_DIR = ROOT / "usr/share/backgrounds/himal"
MASTER = ROOT / "usr/share/himal/credit"
FILES = {}

TAGLINE = "Power by People, Inspired by Nepal"
CREDIT = "Build by Samir Puri"
BRAND = "HIMAL OS"

# Prefer a real TTF so the type is clean. Falls back gracefully.
FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Futura.ttc",
    "/System/Library/Fonts/Supplemental/Avenir Next.ttc",
    "/System/Library/Fonts/Supplemental/Helvetica.ttc",
    "/System/Library/Fonts/HelveticaNeue.ttc",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/SFNS.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def load_font(size):
    for p in FONT_CANDIDATES:
        if pathlib.Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    try:
        return ImageFont.load_default(size)
    except TypeError:
        return ImageFont.load_default()


def tracked(draw, xy, text, font, fill, tracking):
    """Draw letter-spaced text — small caps with air reads as designed, not stamped."""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + tracking
    return x


def tracked_width(draw, text, font, tracking):
    return sum(draw.textlength(c, font=font) for c in text) + tracking * (len(text) - 1)


def add_credit(img, dark_text=False):
    """Composite the credit onto a wallpaper, bottom-centred."""
    d = ImageDraw.Draw(img, "RGBA")
    w, h = img.size

    brand_size = max(18, h // 62)
    credit_size = max(13, h // 92)
    tagline_size = max(12, h // 104)

    brand_font = load_font(brand_size)
    credit_font = load_font(credit_size)
    tagline_font = load_font(tagline_size)

    brand_tr = brand_size * 0.42
    credit_tr = credit_size * 0.06
    tagline_tr = tagline_size * 0.05

    if dark_text:
        fg = (16, 32, 64, 190)
        dim = (16, 32, 64, 130)
        faint = (16, 32, 64, 105)
        rule = (18, 104, 168, 150)
    else:
        fg = (255, 255, 255, 205)
        dim = (226, 238, 250, 150)
        faint = (198, 219, 238, 120)
        rule = (22, 152, 210, 170)

    bw = tracked_width(d, BRAND, brand_font, brand_tr)
    cw = d.textlength(CREDIT, font=credit_font)
    tw = d.textlength(TAGLINE, font=tagline_font)

    base_y = h - int(h * 0.085)
    rule_w = int(max(bw, cw) + h * 0.045)
    rule_y = base_y - int(h * 0.028)

    # thin accent rule above the credit — the one decorative element
    d.line([(w // 2 - rule_w // 2, rule_y), (w // 2 + rule_w // 2, rule_y)],
           fill=rule, width=max(1, h // 720))

    tracked(d, (w // 2 - bw // 2, base_y), BRAND, brand_font, fg, brand_tr)
    d.text((w // 2 - cw // 2, base_y + int(brand_size * 2.15)), CREDIT,
           font=credit_font, fill=dim)
    d.text((w // 2 - tw // 2, base_y + int(brand_size * 2.15 + credit_size * 1.6)),
           TAGLINE, font=tagline_font, fill=faint)
    return img


def regenerate_wallpapers():
    print("--- wallpapers with the credit baked in ---")
    BG_DIR.mkdir(parents=True, exist_ok=True)
    for name, (top, bottom, alpha) in WALLPAPERS.items():
        w, h = 2560, 1440
        raw = gradient_wallpaper(w, h, top, bottom, alpha)
        img = Image.frombytes("RGB", (w, h), raw)
        # the light 'ice' variant needs dark type to stay legible
        img = add_credit(img, dark_text=("ice" in name))
        p = BG_DIR / f"{name}.png"
        img.save(p, "PNG", optimize=True)
        print(f"  {p}")

    # a plain default too, so the desktop always has a credited wallpaper
    w, h = 2560, 1440
    raw = gradient_wallpaper(w, h, (0x05, 0x0A, 0x1C), (0x0A, 0x1E, 0x3C), 0.20)
    img = Image.frombytes("RGB", (w, h), raw)
    add_credit(img)
    img.save(BG_DIR / "himal-wallpaper-2560x1440.png", "PNG", optimize=True)
    print(f"  {BG_DIR}/himal-wallpaper-2560x1440.png")


CREDIT_TXT = r"""
   _   _ _                 _      ___  ____
  | | | (_)_ __ ___   __ _| |    / _ \/ ___|
  | |_| | | '_ ` _ \ / _` | |   | | | \___ \
  |  _  | | | | | | | (_| | |   | |_| |___) |
  |_| |_|_|_| |_| |_|\__,_|_|    \___/|____/

  Himal OS 13   -   arm64   -   Debian-based

  Power by People, Inspired by Nepal

  Built, branded and maintained by
        Samir Puri

  This file is part of Himal OS and is protected against removal.
  Delete it and it will be restored automatically.

  Contact the developer: Samir Puri
  Project: Himal OS

"""

CREDIT_MD = f"""# Himal OS

> {TAGLINE}

**{CREDIT}**

---

Himal OS is a Debian 13 (trixie) arm64 system, rebuilt, branded and extended.
It keeps Debian's tested foundation and adds its own desktop components,
configuration tools and Nepal-focused defaults.

## What is here

| Tool | What it does |
|---|---|
| `himal` | system info, layouts, wallpapers, appearance |
| `himal-launcher` | application launcher and power controls |
| `himal-control-center` | quick settings: network, audio, brightness |
| `himal-studio` | themes, wallpapers, icons, layouts |
| `himal-dashboard` | CPU, memory, disk, network, updates |
| `himal-security` | firewall, updates, ports, hardening |
| `himal-recovery` | snapshots and guided repair |
| `himal-performance` | Eco / Balanced / Performance |

## Credit

This system was built by **Samir Puri**.
The name is part of the desktop wallpaper, the boot splash, the login screen,
the About window and this file.

---

*{CREDIT}*
"""


def main():
    regenerate_wallpapers()

    print("\n--- master credit files (root-owned) ---")
    MASTER.mkdir(parents=True, exist_ok=True)
    for name, body in (("HIMAL-OS-CREDIT.txt", CREDIT_TXT),
                       ("HIMAL-OS-CREDIT.md", CREDIT_MD)):
        p = MASTER / name
        p.write_text(body, encoding="utf-8")
        print(f"  {p}")

    print("\n--- installed guard, icon and service ---")
    for path, (content, mode) in GENERATED.items():
        p = pathlib.Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        os.chmod(p, mode)
        print(f"  {path}")


GENERATED = {
    str(ROOT / "usr/local/bin/himal-credit-guard"): (r"""#!/bin/sh
# Restore the Himal OS developer credit if it has been removed or edited.
# Build by Samir Puri
MASTER=/usr/share/himal/credit
TARGETS="$HOME/HIMAL-OS-CREDIT.txt $HOME/HIMAL-OS-CREDIT.md $HOME/.config/himal/CREDIT"
mkdir -p "$HOME/.config/himal" 2>/dev/null

for f in HIMAL-OS-CREDIT.txt HIMAL-OS-CREDIT.md; do
    src="$MASTER/$f"
    dst="$HOME/$f"
    [ -r "$src" ] || continue
    if ! cmp -s "$src" "$dst" 2>/dev/null; then
        cp -f "$src" "$dst" 2>/dev/null || continue
        chmod 444 "$dst" 2>/dev/null
        # immutable: blocks deletion and edits even by root until the attribute is cleared
        chattr +i "$dst" 2>/dev/null
    fi
done

# marker
marker="$HOME/.config/himal/CREDIT"
if ! grep -q "Samir Puri" "$marker" 2>/dev/null; then
    printf 'Himal OS\nBuild by Samir Puri\n' > "$marker" 2>/dev/null
    chmod 444 "$marker" 2>/dev/null
fi

# desktop icon
desk="$HOME/Desktop"
if [ -d "$desk" ]; then
    icon="$desk/Build by Samir Puri.desktop"
    if [ ! -f "$icon" ]; then
        cp -f /usr/share/applications/himal-credit.desktop "$icon" 2>/dev/null
        chmod 444 "$icon" 2>/dev/null
        chattr +i "$icon" 2>/dev/null
    fi
    chmod +x "$icon" 2>/dev/null
    if command -v xfconf-query >/dev/null 2>&1; then
        xfconf-query -c xfce4-desktop -p /desktop-icons/file-icons/show-filesystem -n -t bool -s true 2>/dev/null
        xfconf-query -c xfce4-desktop -p /desktop-icons/file-icons/show-home -n -t bool -s true 2>/dev/null
    fi
fi
exit 0
""", 0o755),

    str(ROOT / "usr/share/applications/himal-credit.desktop"): ("""\
[Desktop Entry]
Type=Application
Name=Build by Samir Puri
Comment=Himal OS - Power by People, Inspired by Nepal
Exec=himal about
Icon=himal-logo
Terminal=false
Categories=System;
""", 0o644),

    str(ROOT / "etc/systemd/system/himal-credit.service"): ("""\
[Unit]
Description=Restore the Himal OS developer credit
After=local-fs.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/himal-credit-guard
""", 0o644),

    str(ROOT / "etc/systemd/system/himal-credit.timer"): ("""\
[Unit]
Description=Keep the Himal OS developer credit in place

[Timer]
OnBootSec=1min
OnUnitActiveSec=5min
Persistent=true

[Install]
WantedBy=timers.target
""", 0o644),

    str(ROOT / "etc/xdg/autostart/himal-credit.desktop"): ("""\
[Desktop Entry]
Type=Application
Name=Himal OS Credit
Comment=Keep the developer credit in place
Exec=/usr/local/bin/himal-credit-guard
Terminal=false
NoDisplay=true
X-GNOME-Autostart-enabled=true
""", 0o644),
}


if __name__ == "__main__":
    main()
