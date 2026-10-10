#!/usr/bin/env python3
"""Brand the GRUB boot menu, which otherwise renders "Debian GNU/Linux 13 (trixie)".

live-build builds that banner from bootloaders/splash.svg, substituting
@PROJECT@ @VERSION@ (@DISTRIBUTION@) - and 'lb config' has no --project option,
so the only reliable override is to supply our own splash image and theme.

Writes:
  config/includes.binary/boot/grub/splash.png          our background
  config/bootloaders/grub-pc/live-theme/theme.txt      Himal title + colours
  config/includes.binary/boot/grub/live-theme/theme.txt

Credit: Build by Samir Puri
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from make_assets import render_wallpaper, write_png  # noqa: E402

SPLASH_W, SPLASH_H = 1024, 768

THEME = """\
# Himal OS GRUB theme - overrides live-build's default Debian banner
# Credit: Build by Samir Puri
desktop-image: "../splash.png"
title-color: "#1698D2"
title-font: "Unifont Regular 16"
title-text: "Himal OS 13   (arm64)"
message-font: "Unifont Regular 16"
terminal-font: "Unifont Regular 16"

# help bar at the bottom
+ label {
    top = 100%-50
    left = 0
    width = 100%
    height = 20
    text = "@KEYMAP_SHORT@"
    align = "center"
    color = "#a8a8a8"
    font = "Unifont Regular 16"
}

# boot menu
+ boot_menu {
    left = 10%
    width = 80%
    top = 52%
    height = 48%-80
    item_color = "#c8c8c8"
    item_font = "Unifont Regular 16"
    selected_item_color = "#1698D2"
    selected_item_font = "Unifont Regular 16"
    item_height = 16
    item_padding = 0
    item_spacing = 4
    icon_width = 0
    icon_heigh = 0
    item_icon_space = 0
}

# timeout progress bar
+ progress_bar {
    id = "__timeout__"
    left = 15%
    top = 100%-80
    height = 16
    width = 70%
    font = "Unifont Regular 16"
    text_color = "#081430"
    fg_color = "#1698D2"
    bg_color = "#070E2A"
    border_color = "#1698D2"
    text = "@TIMEOUT_NOTIFICATION_LONG@"
}
"""


def main():
    # 1. the splash background: dark Himal gradient with the badge watermark
    splash = pathlib.Path("config/includes.binary/boot/grub/splash.png")
    n = write_png(splash, SPLASH_W, SPLASH_H, render_wallpaper(SPLASH_W, SPLASH_H))
    print(f"  {splash} ({SPLASH_W}x{SPLASH_H}, {n} bytes)")

    # 2. the theme, in both the template dir and the binary tree
    for p in (pathlib.Path("config/bootloaders/grub-pc/live-theme/theme.txt"),
              pathlib.Path("config/includes.binary/boot/grub/live-theme/theme.txt")):
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(THEME, encoding="utf-8")
        print(f"  {p} ({len(THEME)} bytes)")

    print("\nGRUB menu will read 'Himal OS 13   (arm64)' instead of the Debian banner.")


if __name__ == "__main__":
    main()
