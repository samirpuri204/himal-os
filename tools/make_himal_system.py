#!/usr/bin/env python3
"""Himal OS system layer: Nepal-first defaults, safer beginner defaults,
application menu entries, and the extended `himal` command.

Credit: Build by Samir Puri
"""
import os
import pathlib

ROOT = pathlib.Path("config/includes.chroot")
HOOKS = pathlib.Path("config/hooks/normal")
APPS = ROOT / "usr/share/applications"
FILES = {}

# Nepali names for the current date. Weekday and month names are stable;
# full Bikram Sambat conversion needs an authoritative month-length table and is
# deliberately not faked here.
CALENDAR = r'''#!/bin/sh
# himal-calendar - the date, in Nepali as well as English.
# Build by Samir Puri
set -u
dow=$(date +%w)
mon=$(date +%m)

case "$dow" in
    0) ne_dow="आइतबार" ;;
    1) ne_dow="सोमबार" ;;
    2) ne_dow="मंगलबार" ;;
    3) ne_dow="बुधबार" ;;
    4) ne_dow="बिहीबार" ;;
    5) ne_dow="शुक्रबार" ;;
    6) ne_dow="शनिबार" ;;
esac

case "$mon" in
    01) ne_mon="जनवरी" ;; 02) ne_mon="फेब्रुअरी" ;; 03) ne_mon="मार्च" ;;
    04) ne_mon="अप्रिल" ;; 05) ne_mon="मे" ;; 06) ne_mon="जुन" ;;
    07) ne_mon="जुलाई" ;; 08) ne_mon="अगस्ट" ;; 09) ne_mon="सेप्टेम्बर" ;;
    10) ne_mon="अक्टोबर" ;; 11) ne_mon="नोभेम्बर" ;; 12) ne_mon="डिसेम्बर" ;;
esac

printf '  %s\n' "$(date '+%A, %d %B %Y')"
printf '  %s %s %s\n' "$ne_dow" "$(date +%d)" "$ne_mon"
printf '  %s\n' "$(date '+%H:%M %Z')"
'''

APPMENU = [
    ("himal-control-center", "Himal Control Center",
     "Quick settings: network, sound, appearance and power", "preferences-system"),
    ("himal-studio", "Himal Personalization Studio",
     "Themes, wallpapers, icons and desktop layouts", "preferences-desktop-theme"),
    ("himal-dashboard", "Himal System Dashboard",
     "CPU, memory, storage, network and updates", "utilities-system-monitor"),
    ("himal-security", "Himal Security Center",
     "Firewall, updates, open ports and hardening", "security-high"),
    ("himal-recovery", "Himal Recovery System",
     "Snapshots, repair and rollback", "drive-harddisk"),
    ("himal-performance", "Himal Performance Mode",
     "Eco, Balanced and Performance profiles", "power-profile-balanced"),
    ("himal-apphub", "Himal Universal App Hub",
     "APT, Flatpak and AppImage in one place", "system-software-install"),
    ("himal-launcher", "Himal Launcher",
     "Application search and power controls", "system-search"),
]


def add(path, content, mode=0o644, root=ROOT):
    FILES[str(root / path)] = (content, mode)


# ------------------------------------------------------------------ Nepal-first
add("etc/default/locale", """\
LANG=en_US.UTF-8
LANGUAGE=en_US:en
LC_TIME=en_US.UTF-8
LC_NUMERIC=en_US.UTF-8
""")

add("etc/default/keyboard", """\
# Himal OS - Nepali and English layouts, switch with Super+Space
XKBMODEL="pc105"
XKBLAYOUT="us,np"
XKBVARIANT=","
XKBOPTIONS="grp:win_space_toggle"
BACKSPACE="guess"
""")

add("etc/locale.gen.d/himal.conf", """\
# Himal OS - generate both the working locale and Nepali
en_US.UTF-8 UTF-8
ne_NP UTF-8
""")

add("usr/local/bin/himal-calendar", CALENDAR, 0o755)

# ------------------------------------------------------------------ safer defaults
add("etc/apt/apt.conf.d/20auto-upgrades", """\
// Himal OS - automatic security updates, enabled by default.
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
""")

add("etc/apt/apt.conf.d/51-himal-safer", """\
// Himal OS - never remove the running kernel or pull in removals unattended.
Unattended-Upgrade::Remove-Unused-Kernel-Packages "false";
Unattended-Upgrade::Remove-Unused-Dependencies "false";
Unattended-Upgrade::MinimalSteps "true";
""")

add("etc/ufw/ufw.conf", """\
ENABLED=yes
LOGLEVEL=low
IPV6=yes
""")

add("etc/ufw/user.rules", """\
*filter
:ufw-user-input - [0:0]
:ufw-user-output - [0:0]
:ufw-user-forward - [0:0]
### RULES ###
### tuple ### allow any 22 0.0.0.0/0 any 0.0.0.0/0 in
-A ufw-user-input -p tcp --dport 22 -j ACCEPT
### END RULES ###
-A ufw-user-input -j DROP
-A ufw-user-output -j ACCEPT
-A ufw-user-forward -j DROP
COMMIT
""")

add("etc/ufw/user6.rules", """\
*filter
:ufw6-user-input - [0:0]
:ufw6-user-output - [0:0]
:ufw6-user-forward - [0:0]
-A ufw6-user-input -j DROP
-A ufw6-user-output -j ACCEPT
-A ufw6-user-forward -j DROP
COMMIT
""")

add("etc/xdg/autostart/himal-firstboot.desktop", """\
[Desktop Entry]
Type=Application
Name=Himal OS First Boot
Comment=Apply the default firewall policy on first login
Exec=/usr/local/bin/himal-firstboot
Terminal=false
NoDisplay=true
X-GNOME-Autostart-enabled=true
""")

add("usr/local/bin/himal-firstboot", r"""#!/bin/sh
# Apply Himal OS safe defaults once. Build by Samir Puri
FLAG=$HOME/.config/himal/firstboot
[ -f "$FLAG" ] && exit 0
mkdir -p "$(dirname "$FLAG")" 2>/dev/null

# firewall on, deny incoming by default (already encoded in /etc/ufw/user.rules)
if command -v ufw >/dev/null 2>&1; then
    pkexec ufw --force enable >/dev/null 2>&1 || true
fi

touch "$FLAG"
exit 0
""", 0o755)

# ------------------------------------------------------------------ menu entries
for cmd, title, comment, icon in APPMENU:
    add(f"usr/share/applications/{cmd}.desktop", f"""\
[Desktop Entry]
Type=Application
Name={title}
Comment={comment}
Exec={cmd}
Icon={icon}
Terminal=false
Categories=System;Settings;X-Himal;
Keywords=himal;{cmd.replace('himal-', '')};
""")

# the launcher keeps the Himal mark, everything else uses a themed icon
add("usr/share/applications/himal-launcher.desktop", """\
[Desktop Entry]
Type=Application
Name=Himal Launcher
Comment=Application search and power controls
Exec=himal-launcher
Icon=himal-logo
Terminal=false
Categories=System;Utility;
""")

# ------------------------------------------------------------------ hook
FILES[str(HOOKS / "0700-himal-system.hook.chroot")] = (r"""#!/bin/sh
# Himal OS system layer: timezone, locales, firewall, automatic updates.
# Build by Samir Puri
set -e

# Nepal timezone by default
if [ -f /usr/share/zoneinfo/Asia/Kathmandu ]; then
    ln -sf /usr/share/zoneinfo/Asia/Kathmandu /etc/localtime
    echo "Asia/Kathmandu" > /etc/timezone
    echo "himal: timezone set to Asia/Kathmandu"
fi

# generate locales (en_US plus Nepali)
if command -v locale-gen >/dev/null 2>&1; then
    locale-gen en_US.UTF-8 ne_NP 2>/dev/null || locale-gen 2>/dev/null || true
fi

# enable the firewall at boot rather than waiting for first login
if command -v ufw >/dev/null 2>&1; then
    ufw --force enable >/dev/null 2>&1 || true
fi

# automatic security updates
systemctl enable unattended-upgrades 2>/dev/null || true
systemctl enable apt-daily.timer apt-daily-upgrade.timer 2>/dev/null || true

# trim and index new executables so the menu picks up the Himal tools
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q /usr/share/applications 2>/dev/null || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor 2>/dev/null || true
fi

echo "himal: system layer applied"
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
