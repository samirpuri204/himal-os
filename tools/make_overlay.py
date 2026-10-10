#!/usr/bin/env python3
"""Write the Himal OS branding overlay into config/includes.chroot/.

Covers the surfaces a user actually sees: login banner, OS identity, desktop
theme, wallpaper, dock, greeter, and the two switchable panel layouts.

Credit: Build by Samir Puri
"""
import os
import pathlib
import stat

ROOT = pathlib.Path("config/includes.chroot")
ETC = ROOT / "etc"
XDG = ETC / "xdg/xfce4/xfconf/xfce-perchannel-xml"

WALL = "/usr/share/backgrounds/himal/himal-wallpaper-2560x1440.png"
LOGO = "/usr/share/pixmaps/himal-logo-256.png"

FILES = {}


def add(path, content, mode=0o644):
    FILES[str(path)] = (content, mode)


# ------------------------------------------------------------------ identity
add(ETC / "os-release", """\
PRETTY_NAME="Himal OS 13"
NAME="Himal OS"
VERSION_ID="13"
VERSION="13 (trixie)"
VERSION_CODENAME=trixie
ID=himal
ID_LIKE=debian
DEBIAN_CODENAME=trixie
ANSI_COLOR="0;34"
LOGO=himal-logo
BUILD_BY="Samir Puri"
HOME_URL=""
SUPPORT_URL=""
""")

# getty interprets backslash escapes in /etc/issue (\n = hostname, \l = tty), so a
# literal backslash must be written as a doubled one or getty swallows it and the
# ASCII art comes out mangled.
add(ETC / "issue", r"""
   _   _ _                 _      ___  ____
  | | | (_)_ __ ___   __ _| |    / _ \\/ ___|
  | |_| | | '_ ` _ \\ / _` | |   | | | \\___ \\
  |  _  | | | | | | | (_| | |   | |_| |___) |
  |_| |_|_|_| |_| |_|\\__,_|_|    \\___/|____/

  Himal OS 13 (trixie)  -  arm64  -  \n \l
  Build by Samir Puri
""")

add(ETC / "issue.net", "Himal OS 13 (trixie) - Build by Samir Puri\n")

add(ETC / "hostname", "himal\n")

add(ETC / "hosts", """\
127.0.0.1\tlocalhost
127.0.1.1\thimal
::1\t\tlocalhost ip6-localhost ip6-loopback
ff02::1\t\tip6-allnodes
ff02::2\t\tip6-allrouters
""")

add(ETC / "lsb-release", """\
DISTRIB_ID=Himal OS
DISTRIB_DESCRIPTION="Himal OS 13"
""")

# ------------------------------------------------------------------ fastfetch
add(ETC / "fastfetch/config.jsonc", """\
{
  "$schema": "https://github.com/fastfetch-cli/fastfetch/raw/dev/doc/json_schema.json",
  "logo": { "source": "%s", "padding": { "top": 1, "left": 2 } },
  "display": { "separator": "  ", "color": { "keys": "34" } },
  "modules": [
    "title",
    "separator",
    "os",
    "host",
    "kernel",
    "uptime",
    "packages",
    "shell",
    "display",
    "de",
    "wm",
    "terminal",
    "cpu",
    "gpu",
    "memory",
    "disk",
    "localip",
    "break",
    { "type": "custom", "format": "Build by Samir Puri" }
  ]
}
""" % LOGO)

# ------------------------------------------------------------------ desktop theme
add(XDG / "xsettings.xml", """\
<?xml version="1.0" encoding="UTF-8"?>
<channel name="xsettings" version="1.0">
  <property name="Net" type="empty">
    <property name="ThemeName" type="string" value="Arc-Darker"/>
    <property name="IconThemeName" type="string" value="Papirus-Dark"/>
    <property name="EnableEventSounds" type="bool" value="false"/>
    <property name="EnableInputFeedbackSounds" type="bool" value="false"/>
  </property>
  <property name="Xft" type="empty">
    <property name="DPI" type="int" value="96"/>
    <property name="Antialias" type="int" value="1"/>
    <property name="Hintstyle" type="int" value="1"/>
    <property name="RGBA" type="int" value="1"/>
  </property>
</channel>
""")

# macOS convention: window buttons on the LEFT
add(XDG / "xfwm4.xml", """\
<?xml version="1.0" encoding="UTF-8"?>
<channel name="xfwm4" version="1.0">
  <property name="general" type="empty">
    <property name="theme" type="string" value="Arc-Darker"/>
    <property name="title_font" type="string" value="Noto Sans Bold 10"/>
    <property name="button_layout" type="string" value="O|SHMC"/>
    <property name="button_offset" type="int" value="8"/>
    <property name="button_spacing" type="int" value="6"/>
    <property name="click_to_focus" type="bool" value="false"/>
    <property name="snap_to_border" type="bool" value="true"/>
    <property name="snap_to_windows" type="bool" value="true"/>
    <property name="workspace_count" type="int" value="4"/>
  </property>
</channel>
""")

add(XDG / "xfce4-desktop.xml", """\
<?xml version="1.0" encoding="UTF-8"?>
<channel name="xfce4-desktop" version="1.0">
  <property name="backdrop" type="empty">
    <property name="screen0" type="empty">
      <property name="monitor0" type="empty">
        <property name="workspace0" type="empty">
          <property name="last-image" type="string" value="%s"/>
          <property name="image-style" type="int" value="5"/>
        </property>
      </property>
    </property>
  </property>
  <property name="desktop-icons" type="empty">
    <property name="style" type="int" value="2"/>
    <property name="file-icons" type="empty">
      <property name="show-home" type="bool" value="false"/>
      <property name="show-filesystem" type="bool" value="false"/>
      <property name="show-trash" type="bool" value="false"/>
    </property>
  </property>
</channel>
""" % WALL)

# ------------------------------------------------------------------ panel (macOS layout)
# Top bar: app menu left, clock centre-ish, status right. Dock lives in Plank.
add(XDG / "xfce4-panel.xml", """\
<?xml version="1.0" encoding="UTF-8"?>
<channel name="xfce4-panel" version="1.0">
  <property name="configver" type="int" value="2"/>
  <property name="panels" type="array">
    <value type="int" value="1"/>
    <property name="panel-1" type="empty">
      <property name="position" type="string" value="p=6;x=0;y=0"/>
      <property name="length" type="uint" value="100"/>
      <property name="position-locked" type="bool" value="true"/>
      <property name="size" type="uint" value="30"/>
      <property name="icon-size" type="uint" value="18"/>
      <property name="background-alpha" type="uint" value="90"/>
      <property name="plugin-ids" type="array">
        <value type="int" value="1"/>
        <value type="int" value="2"/>
        <value type="int" value="3"/>
        <value type="int" value="4"/>
        <value type="int" value="5"/>
        <value type="int" value="6"/>
      </property>
    </property>
  </property>
  <property name="plugins" type="empty">
    <property name="plugin-1" type="string" value="whiskermenu">
      <property name="button-icon" type="string" value="himal-logo"/>
    </property>
    <property name="plugin-2" type="string" value="separator">
      <property name="expand" type="bool" value="true"/>
      <property name="style" type="uint" value="0"/>
    </property>
    <property name="plugin-3" type="string" value="clock">
      <property name="digital-layout" type="uint" value="1"/>
      <property name="digital-time-font" type="string" value="Noto Sans 11"/>
      <property name="digital-date-font" type="string" value="Noto Sans 9"/>
    </property>
    <property name="plugin-4" type="string" value="separator">
      <property name="expand" type="bool" value="true"/>
      <property name="style" type="uint" value="0"/>
    </property>
    <property name="plugin-5" type="string" value="systray">
      <property name="icon-size" type="uint" value="16"/>
    </property>
    <property name="plugin-6" type="string" value="pulseaudio">
      <property name="enable-keyboard-shortcuts" type="bool" value="true"/>
    </property>
  </property>
</channel>
""")

# ------------------------------------------------------------------ plank dock
add(ETC / "xdg/plank/dock1/settings", """\
[PlankDockPreferences]
Alignment=3
DockItems=exo-file-manager.dockitem;;firefox-esr.dockitem;;chromium.dockitem;;xfce4-terminal.dockitem;;mousepad.dockitem;;org.gnome.Software.dockitem
HideMode=0
IconSize=48
ItemsAlignment=3
LockItems=false
PinnedOnly=false
Position=3
Theme=Transparent
ZoomEnabled=true
ZoomPercent=150
""")

add(ETC / "xdg/autostart/plank.desktop", """\
[Desktop Entry]
Type=Application
Name=Plank
Comment=Himal OS dock
Exec=plank
Icon=plank
Terminal=false
Categories=Utility;
X-GNOME-Autostart-enabled=true
""")

# ------------------------------------------------------------------ layout switcher
add(ROOT / "usr/local/bin/himal-layout", """\
#!/bin/sh
# Switch the Himal OS desktop between macOS-style and Windows-style layouts.
#   himal-layout mac      (default) top bar + bottom dock, controls on the left
#   himal-layout windows  bottom taskbar + Start menu, controls on the right
set -e
case "${1:-}" in
  mac)
    xfconf-query -c xfce4-panel -p /panels/panel-1/position -s "p=6;x=0;y=0"
    xfconf-query -c xfce4-panel -p /panels/panel-1/size -s 30
    xfconf-query -c xfwm4 -p /general/button_layout -s "O|SHMC"
    [ -f /etc/xdg/autostart/plank.desktop ] && cp /etc/xdg/autostart/plank.desktop "$HOME/.config/autostart/" 2>/dev/null || true
    (plank >/dev/null 2>&1 &) || true
    echo "Himal OS: macOS-style layout applied"
    ;;
  windows)
    xfconf-query -c xfce4-panel -p /panels/panel-1/position -s "p=10;x=0;y=0"
    xfconf-query -c xfce4-panel -p /panels/panel-1/size -s 38
    xfconf-query -c xfwm4 -p /general/button_layout -s "|HMC"
    pkill -x plank 2>/dev/null || true
    echo "Himal OS: Windows-style layout applied"
    ;;
  *)
    echo "usage: himal-layout {mac|windows}" >&2
    exit 1
    ;;
esac
xfce4-panel -r >/dev/null 2>&1 || true
""", 0o755)

# ------------------------------------------------------------------ greeter
# NOTE: this string IS %-formatted, so %% is needed for a literal percent.
# Without the '% WALL' at the end these stay literal and the greeter is broken.
add(ETC / "lightdm/lightdm-gtk-greeter.conf.d/50-himal.conf", """\
[greeter]
background=%s
theme-name=Arc-Darker
icon-theme-name=Papirus-Dark
font-name=Noto Sans 11
xft-antialias=true
xft-hintstyle=hintslight
xft-rgba=rgb
default-user-image=/usr/share/pixmaps/himal-logo-greeter.png
indicators=~host;~spacer;~clock;~spacer;~session;~language;~power
clock-format=%%H:%%M
position=50%%,center 62%%
""" % WALL)

# ------------------------------------------------------------------ desktop entry
add(ROOT / "usr/share/applications/himal-layout.desktop", """\
[Desktop Entry]
Type=Application
Name=Himal OS Layout
Comment=Switch between macOS-style and Windows-style desktop layouts
Exec=himal-layout-switch
Icon=himal-logo
Terminal=true
Categories=Settings;DesktopSettings;
""")

add(ROOT / "usr/local/bin/himal-layout-switch", """\
#!/bin/sh
# Minimal chooser so the layout can be switched without a terminal.
choice=$(printf 'macOS-style layout\\nWindows-style layout\\n' | \\
  zenity --list --title="Himal OS Layout" --text="Choose a desktop layout" \\
         --column="Layout" --height=220 --width=320 2>/dev/null) || exit 0
case "$choice" in
  "macOS-style layout")   exec himal-layout mac ;;
  "Windows-style layout") exec himal-layout windows ;;
esac
""", 0o755)


# Xfce keys the desktop backdrop to the real monitor connector name
# (monitorVirtual-1, monitorHDMI-1, ...). A static config that only sets the
# 'monitor0' fallback silently does nothing, which is why the first build came up
# with the Debian default wallpaper despite the file and config both being correct.
add(ROOT / "usr/local/bin/himal-set-wallpaper", """\
#!/bin/sh
# Apply the Himal OS wallpaper to whatever displays actually exist.
WALL=/usr/share/backgrounds/himal/himal-wallpaper-2560x1440.png

set_prop() { # set_prop <property> <type> <value>
    xfconf-query -c xfce4-desktop -p "$1" -n -t "$2" -s "$3" 2>/dev/null || \\
    xfconf-query -c xfce4-desktop -p "$1"    -t "$2" -s "$3" 2>/dev/null
}

outs=$(xrandr --listmonitors 2>/dev/null | awk 'NR>1 {print $NF}')
[ -z "$outs" ] && outs="monitor0"

for out in $outs monitor0; do
    base="/backdrop/screen0/$out/workspace0"
    set_prop "$base/last-image"  string "$WALL"
    set_prop "$base/image-style" int    5
done
exit 0
""", 0o755)

add(ETC / "xdg/autostart/himal-wallpaper.desktop", """\
[Desktop Entry]
Type=Application
Name=Himal OS Wallpaper
Comment=Apply the Himal OS desktop background
Exec=/usr/local/bin/himal-set-wallpaper
Terminal=false
NoDisplay=true
X-GNOME-Autostart-enabled=true
""")


def main():
    for path, (content, mode) in FILES.items():
        p = pathlib.Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        os.chmod(p, mode)
        print(f"  {path}  ({len(content)} bytes)")
    print(f"\n{len(FILES)} overlay files written.")


if __name__ == "__main__":
    main()
