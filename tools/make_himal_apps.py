#!/usr/bin/env python3
"""What makes Himal OS different from stock Debian.

Generates the pieces a user actually interacts with:

  * `himal` - a real CLI (info / about / features / layout / wallpaper / accent)
  * a first-login Welcome window, branded, shown once
  * a branded login banner and shell prompt
  * Himal entries in the application menu and the desktop right-click menu
  * the Plymouth theme selection hook

Credit: Build by Samir Puri
"""
import os
import pathlib

ROOT = pathlib.Path("config/includes.chroot")
HOOKS = pathlib.Path("config/hooks/normal")
FILES = {}

ASCII = r"""
   _   _ _                 _      ___  ____
  | | | (_)_ __ ___   __ _| |    / _ \/ ___|
  | |_| | | '_ ` _ \ / _` | |   | | | \___ \
  |  _  | | | | | | | (_| | |   | |_| |___) |
  |_| |_|_|_| |_| |_|\__,_|_|    \___/|____/
"""


def add(path, content, mode=0o644, root=ROOT):
    FILES[str(root / path)] = (content, mode)


# ---------------------------------------------------------------------- CLI
add("usr/local/bin/himal", r"""#!/bin/sh
# himal - the Himal OS control tool
# Build by Samir Puri
set -u

WALL_DIR=/usr/share/backgrounds/himal
WALL_DEFAULT=$WALL_DIR/himal-wallpaper-abyss.png
LOG=$HOME/.config/himal/accent

banner() {
    cat <<'HIMAL_EOF'

   _   _ _                 _      ___  ____
  | | | (_)_ __ ___   __ _| |    / _ \/ ___|
  | |_| | | '_ ` _ \ / _` | |   | | | \___ \
  |  _  | | | | | | | (_| | |   | |_| |___) |
  |_| |_|_|_| |_| |_|\__,_|_|    \___/|____/

         Himal OS 13  -  "Build by Samir Puri"
HIMAL_EOF
}

cmd_info() {
    banner
    echo
    printf '  %-14s %s\n' "OS"        "$(grep -m1 PRETTY_NAME /etc/os-release | cut -d= -f2 | tr -d '\"')"
    printf '  %-14s %s\n' "Kernel"    "$(uname -r)"
    printf '  %-14s %s\n' "Arch"      "$(uname -m)"
    printf '  %-14s %s\n' "Host"      "$(cat /etc/hostname 2>/dev/null)"
    printf '  %-14s %s\n' "Desktop"   "Xfce  ($(himal-layout 2>/dev/null || echo 'top bar + dock'))"
    printf '  %-14s %s\n' "Uptime"    "$(uptime -p 2>/dev/null | sed 's/^up //')"
    printf '  %-14s %s\n' "Packages"  "$(dpkg-query -f '.\n' -W 2>/dev/null | wc -l)"
    printf '  %-14s %s\n' "Memory"    "$(free -h 2>/dev/null | awk '/^Mem:/{print $3" / "$2}')"
    printf '  %-14s %s\n' "Developer" "Samir Puri"
    echo
    echo "  Run 'himal help' to see what else this system can do."
    echo
}

cmd_features() {
    banner
    cat <<'HIMAL_EOF'

  What makes Himal OS different from the Debian it is built on

  [1] himal - one command for system info, layout, wallpaper and appearance.
  [2] Two desktop layouts, switchable live: a macOS-style top bar with a dock,
      or a Windows-style bottom taskbar. No reinstall, no second image.
  [3] Four Himal wallpapers (abyss, dusk, ice, ember) plus light/dark accent.
  [4] A Windows-style boot splash with the Himal mark, carrying the developer
      credit on screen at every start.
  [5] A first-run Welcome window, shown once.
  [6] Security toolkit preinstalled: nmap, wireshark, john, aircrack-ng, ufw.
  [7] Development stack preinstalled: git, python3, nodejs, build tools.
  [8] Flatpak + Flathub ready, so any app is one command away.
  [9] The Himal identity throughout: boot menu, splash, login, terminal,
      system info and GRUB - not stock Debian anywhere it matters.

  Built and branded by Samir Puri.
HIMAL_EOF
}

cmd_layout() {
    case "${1:-}" in
        mac|macos|macos-style)   himal-layout mac ;;
        windows|win)             himal-layout windows ;;
        "")                      himal-layout 2>/dev/null; echo "Usage: himal layout {mac|windows}" ;;
        *)                       echo "Unknown layout: $1" >&2; exit 1 ;;
    esac
}

cmd_wallpaper() {
    if [ -z "${1:-}" ]; then
        echo "Available wallpapers:"
        for f in "$WALL_DIR"/himal-wallpaper-*.png; do
            [ -e "$f" ] || continue
            b=$(basename "$f" .png | sed 's/himal-wallpaper-//')
            echo "  $b"
        done
        echo
        echo "Set one with: himal wallpaper <name>"
        return 0
    fi
    f="$WALL_DIR/himal-wallpaper-$1.png"
    if [ ! -f "$f" ]; then echo "No such wallpaper: $1" >&2; exit 1; fi
    for out in $(xrandr --listmonitors 2>/dev/null | awk 'NR>1 {print $NF}') monitor0; do
        p="/backdrop/screen0/$out/workspace0/last-image"
        xfconf-query -c xfce4-desktop -p "$p" -n -t string -s "$f" 2>/dev/null || \
        xfconf-query -c xfce4-desktop -p "$p"    -t string -s "$f" 2>/dev/null
    done
    echo "Wallpaper set to: $1"
}

cmd_accent() {
    mkdir -p "$(dirname "$LOG")" 2>/dev/null
    case "${1:-}" in
        dark)
            xfconf-query -c xsettings -p /Net/ThemeName -s Arc-Darker 2>/dev/null || true
            xfconf-query -c xsettings -p /Net/IconThemeName -s Papirus-Dark 2>/dev/null || true
            echo dark > "$LOG" ;;
        light)
            xfconf-query -c xsettings -p /Net/ThemeName -s Arc 2>/dev/null || true
            xfconf-query -c xsettings -p /Net/IconThemeName -s Papirus 2>/dev/null || true
            echo light > "$LOG" ;;
        *)  echo "Usage: himal accent {dark|light}"; return 1 ;;
    esac
    echo "Accent set to: $1"
}

cmd_about() {
    if command -v yad >/dev/null 2>&1; then
        yad --title="About Himal OS" --image=/usr/share/pixmaps/himal-logo-256.png \
            --image-on-top --width=420 \
            --text="<big><b>Himal OS 13</b></big>\n\nA Debian 13 (trixie) arm64 system,\nrebuilt and branded.\n\n<i>Build by Samir Puri</i>"
    else
        zenity --info --title="About Himal OS" --width=380 \
            --text="Himal OS 13\n\nDebian 13 (trixie) arm64\n\nBuild by Samir Puri" 2>/dev/null
    fi
}

cmd_credit() {
    banner
    echo
    echo "  Build by Samir Puri"
    echo
}

cmd_help() {
    banner
    cat <<'HIMAL_EOF'

  Usage: himal [command]

    (nothing) | info      system information
    features              what makes this OS different
    about                 About window
    layout mac|windows    switch desktop layout live
    wallpaper [name]      list or set a Himal wallpaper
    accent dark|light     switch desktop appearance
    credit                who built this

  Desktop tools

    control-center        quick settings: network, sound, power
    studio                themes, wallpapers, icons, layouts
    dashboard             CPU, memory, disk, network, updates
    security              firewall, updates, ports, hardening
    recovery | repair     snapshots and guided repair
    performance           Eco, Balanced, Performance
    apphub                APT, Flatpak and AppImage in one place
    launcher              application search and power controls
    calendar              the date, in Nepali as well as English

    update                update the system
    help                  this text

HIMAL_EOF
}

case "${1:-}" in
    ""|info)     cmd_info ;;
    features)    cmd_features ;;
    about)       cmd_about ;;
    layout)      shift; cmd_layout "$@" ;;
    wallpaper)   shift; cmd_wallpaper "$@" ;;
    accent)      shift; cmd_accent "$@" ;;
    credit)      cmd_credit ;;
    control-center|cc)  exec himal-control-center ;;
    studio)             exec himal-studio ;;
    dashboard)          exec himal-dashboard ;;
    security)           exec himal-security ;;
    recovery|repair)    exec himal-recovery ;;
    performance|perf)   exec himal-performance ;;
    apphub|apps)        exec himal-apphub ;;
    launcher)           exec himal-launcher ;;
    calendar)           exec himal-calendar ;;
    update)      echo "Updating Himal OS..."; sudo apt update && sudo apt full-upgrade -y ;;
    help|--help|-h) cmd_help ;;
    *)           echo "himal: unknown command '$1'" >&2; cmd_help; exit 1 ;;
esac
""", 0o755)

# ---------------------------------------------------------------------- welcome
add("usr/local/bin/himal-welcome", r"""#!/bin/sh
# Shown once, on first login. Build by Samir Puri
FLAG=$HOME/.config/himal/welcomed
[ -f "$FLAG" ] && exit 0
mkdir -p "$(dirname "$FLAG")" 2>/dev/null

TEXT="<big><b>Welcome to Himal OS</b></big>

<i>Build by Samir Puri</i>

Your system is ready. A few things worth knowing:

  <b>himal</b> - open a terminal and run it. System info, layouts,
  wallpapers, light/dark - all in one command.

  <b>Two layouts, switched live.</b> The default is the macOS-style
  top bar with a dock. Prefer Windows? Run:

        himal layout windows

  <b>First-run tip:</b> run <b>himal features</b> to see everything
  that makes this system different."

if command -v yad >/dev/null 2>&1; then
    yad --title="Welcome to Himal OS" \
        --image=/usr/share/pixmaps/himal-logo-128.png \
        --image-on-top --width=640 --height=580 \
        --button="Show me:1" --button="Close:0" \
        --text="$TEXT"
    [ $? -eq 1 ] && command -v xfce4-terminal >/dev/null 2>&1 && \
        xfce4-terminal -e "sh -c 'himal features; exec sh'" &
elif command -v zenity >/dev/null 2>&1; then
    zenity --info --title="Welcome to Himal OS" --width=480 --text="$TEXT" 2>/dev/null
fi
touch "$FLAG"
""", 0o755)

add("etc/xdg/autostart/himal-welcome.desktop", """\
[Desktop Entry]
Type=Application
Name=Welcome to Himal OS
Comment=Shown once, on first login
Exec=/usr/local/bin/himal-welcome
Terminal=false
NoDisplay=true
X-GNOME-Autostart-enabled=true
""")

# ---------------------------------------------------------------------- login banner + prompt
add("etc/motd", ASCII + """
  Himal OS 13  -  arm64  -  Debian-based, rebuilt and branded
  Build by Samir Puri

  Type  himal          for system information
        himal features to see what makes this OS different
        himal help     for everything else

""")

add("etc/profile.d/himal.sh", r"""# Himal OS - branded shell environment. Build by Samir Puri
[ -n "${BASH_VERSION:-}" ] || return 0

# branded prompt: cyan path on Himal navy, with a hex marker
if [ "$(id -u)" -eq 0 ]; then
    PS1='\[\e[38;5;203m\]\u@\h\[\e[0m\] \[\e[38;5;39m\]\w\[\e[0m\] \[\e[38;5;244m\]#\[\e[0m\] '
else
    PS1='\[\e[38;5;39m\]\u@\h\[\e[0m\] \[\e[38;5;250m\]\w\[\e[0m\] \[\e[38;5;39m\]\xE2\xAC\xA2\[\e[0m\] '
fi

# fastfetch banner on login shells only, if present
if [ -n "${HIMAL_BANNER_SHOWN:-}" ]; then :
elif [ -x /usr/bin/fastfetch ] && [ -t 1 ]; then
    export HIMAL_BANNER_SHOWN=1
    fastfetch 2>/dev/null || true
fi
""")

# ---------------------------------------------------------------------- menu entries
for name, title, comment, exec_cmd in [
    ("himal-about", "About Himal OS", "Version, base and developer credit", "himal about"),
    ("himal-features", "Himal OS Features", "What makes this system different", "xfce4-terminal -e 'sh -c \"himal features; exec sh\"'"),
    ("himal-info", "Himal OS System Info", "Branded system information", "xfce4-terminal -e 'sh -c \"himal info; exec sh\"'"),
]:
    add(f"usr/share/applications/{name}.desktop", f"""\
[Desktop Entry]
Type=Application
Name={title}
Comment={comment}
Exec={exec_cmd}
Icon=himal-logo
Terminal=false
Categories=System;Settings;
""")

# ---------------------------------------------------------------------- plymouth config + hook
add("etc/plymouth/plymouthd.conf", """\
[Daemon]
Theme=himal
ShowDelay=0
DeviceTimeout=8
""")

FILES[str(HOOKS / "0500-himal-plymouth.hook.chroot")] = (r"""#!/bin/sh
# Select the Himal OS Plymouth splash and bake it into the initramfs.
#
# live-build copies config/includes.chroot AFTER packages are installed, so the
# initramfs that the kernel package generated does not contain our theme. This
# hook runs later and regenerates it.
set -e

if [ -f /usr/share/plymouth/themes/himal/himal.plymouth ]; then
    update-alternatives --install \
        /usr/share/plymouth/themes/default.plymouth default.plymouth \
        /usr/share/plymouth/themes/himal/himal.plymouth 200 2>/dev/null || true
    update-alternatives --set default.plymouth \
        /usr/share/plymouth/themes/himal/himal.plymouth 2>/dev/null || true
    echo "himal: plymouth theme selected"
fi

update-initramfs -u -k all 2>/dev/null || true
""", 0o755)


def main():
    for path, (content, mode) in FILES.items():
        p = pathlib.Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        os.chmod(p, mode)
        print(f"  {path}")
    print(f"\n{len(FILES)} files written.")


if __name__ == "__main__":
    main()
