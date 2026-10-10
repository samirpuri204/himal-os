#!/usr/bin/env python3
"""Himal Dynamic Desktop — the layer that makes the desktop look nothing like Debian.

  * Picom compositor: rounded corners, real shadows, blur, window fading
  * GTK3 CSS override: Himal accent, rounded controls, subtle translucency
  * Plank: floating, translucent, no-stick dock
  * Rofi: the Himal Launcher (app search, recent files, power controls, shortcuts)

Credit: Build by Samir Puri
"""
import os
import pathlib

ROOT = pathlib.Path("config/includes.chroot")
XDG = ROOT / "etc/xdg"
FILES = {}

ACCENT = "#1698D2"
ACCENT_DIM = "#1268A8"
NAVY = "#070E2A"


def add(path, content, mode=0o644, root=ROOT):
    FILES[str(root / path)] = (content, mode)


# ------------------------------------------------------------------ picom
add("etc/xdg/picom/picom.conf", f"""\
# Himal OS compositor - rounded corners, shadows, blur, fading.
# Build by Samir Puri
backend = "glx";
vsync = true;
mark-wmwin-focused = true;

# --- shadows: this is what gives windows the floating, macOS-like depth ---
shadow = true;
shadow-radius = 22;
shadow-opacity = 0.38;
shadow-offset-x = 0;
shadow-offset-y = 10;
shadow-exclude = [
    "class_g = 'Plank'",
    "class_g = 'Rofi'",
    "class_g = 'Conky'",
    "name = 'Notification'",
    "class_g = 'Xfce4-notifyd'",
    "_NET_WM_STATE@:32a *= '_NET_WM_STATE_HIDDEN'"
];

# --- rounded corners everywhere ---
corner-radius = 12;
rounded-corners-exclude = [
    "class_g = 'Plank'",
    "class_g = 'Xfce4-panel'",
    "window_type = 'dock'"
];

# --- real transparency + blur behind windows ---
blur-method = "dual_kawase";
blur-strength = 6;
blur-background = true;
blur-background-frame = true;
blur-background-fixed = false;
blur-background-exclude = [
    "window_type = 'dock'",
    "window_type = 'desktop'",
    "class_g = 'Plank'",
    "_GTK_FRAME_EXTENTS@:c"
];

# --- smooth window animations ---
fading = true;
fade-in-step = 0.06;
fade-out-step = 0.06;
fade-delta = 6;
detect-rounded-corners = true;
detect-client-opacity = true;

# --- Xfce panel should stay sharp, not blurred ---
opacity-rule = [
    "100:class_g = 'Xfce4-panel'",
    "100:class_g = 'Plank'",
    "100:window_type = 'dock'",
    "100:window_type = 'desktop'",
    "96:class_g = 'Xfce4-terminal'"
];
""")

add("etc/xdg/autostart/himal-compositor.desktop", """\
[Desktop Entry]
Type=Application
Name=Himal Compositor
Comment=Rounded corners, shadows and blur
Exec=picom --config /etc/xdg/picom/picom.conf --daemon
Terminal=false
NoDisplay=true
X-GNOME-Autostart-enabled=true
""")

# ------------------------------------------------------------------ GTK3 look
add("etc/gtk-3.0/gtk.css", f"""\
/* Himal OS GTK3 overrides - accent, rounding, subtle depth.
   Loaded on top of the Arc theme. Build by Samir Puri */

@define-color himal_accent {ACCENT};
@define-color himal_accent_dim {ACCENT_DIM};
@define-color himal_navy {NAVY};

/* rounded controls */
button, entry, spinbutton, combobox button {{
    border-radius: 8px;
    padding: 4px 10px;
    transition: all 140ms ease-out;
}}

button:hover {{
    background-image: none;
    background-color: alpha(@himal_accent, 0.16);
}}

button:active,
button:checked {{
    background-image: none;
    background-color: @himal_accent;
    color: #ffffff;
}}

/* the Himal accent on focus instead of Arc's blue */
entry:focus,
spinbutton:focus,
combobox:focus {{
    border-color: @himal_accent;
    box-shadow: 0 0 0 2px alpha(@himal_accent, 0.35);
}}

/* selection colour */
*:selected,
treeview:selected {{
    background-color: @himal_accent;
    color: #ffffff;
}}

/* menus and popovers: rounded, slightly translucent */
menu, .menu, popover, .popover {{
    border-radius: 10px;
    border: 1px solid alpha(@himal_accent, 0.25);
}}

/* notebook tabs */
notebook > header > tabs > tab:checked {{
    color: @himal_accent;
    border-bottom: 2px solid @himal_accent;
}}

/* scrollbars: slim */
scrollbar slider {{
    border-radius: 8px;
    min-width: 6px;
    min-height: 6px;
    background-color: alpha(@himal_accent_dim, 0.55);
}}
scrollbar slider:hover {{
    background-color: @himal_accent;
}}

/* progress bars in Himal accent */
progressbar progress {{
    background-color: @himal_accent;
    border-radius: 6px;
}}
""")

# ------------------------------------------------------------------ plank dock: floating + translucent
add("etc/xdg/plank/dock1/settings", f"""\
[PlankDockPreferences]
Alignment=3
DockItems=exo-file-manager.dockitem;;firefox-esr.dockitem;;chromium.dockitem;;xfce4-terminal.dockitem;;mousepad.dockitem;;org.gnome.Software.dockitem;;himal-control-center.dockitem
HideMode=1
IconSize=52
ItemsAlignment=3
LockItems=false
PinnedOnly=false
Position=3
Theme=Transparent
ZoomEnabled=true
ZoomPercent=170
Offset=12
""")

# ------------------------------------------------------------------ rofi: the Himal Launcher
add("etc/xdg/rofi/himal.rasi", f"""\
/* Himal Launcher - rofi theme. Build by Samir Puri */
configuration {{
    modi: "drun,run,window,filebrowser,ssh,combi";
    combi-modi: "window,drun,run";
    show-icons: true;
    icon-theme: "Papirus-Dark";
    drun-display-format: "{{name}}";
    display-drun: "  Applications";
    display-run: "  Run";
    display-window: "  Windows";
    display-combi: "  Himal Launcher";
    display-filebrowser: "  Files";
    display-ssh: "  SSH";
    font: "Noto Sans 12";
}}

* {{
    bg:      {NAVY}ee;
    bg-alt:  {NAVY}cc;
    fg:      #e8eef7;
    accent:  {ACCENT};
    urgent:  #e05a6a;
    background-color: transparent;
    text-color: @fg;
    border-color: @accent;
    spacing: 0;
}}

window {{
    width: 620px;
    border: 1px solid;
    border-color: @border-color;
    border-radius: 14px;
    background-color: @bg;
    padding: 14px;
}}

inputbar {{
    background-color: @bg-alt;
    border-radius: 10px;
    padding: 10px 14px;
    children: [ prompt, entry ];
}}

prompt {{ text-color: @accent; margin: 0 10px 0 0; }}
entry  {{ placeholder: "Search applications, files and commands..."; placeholder-color: #6b7d92; }}

listview {{ lines: 10; columns: 1; scrollbar: false; margin: 12px 0 0 0; }}

element {{
    padding: 8px 10px;
    border-radius: 8px;
    spacing: 10px;
}}

element selected {{
    background-color: @accent;
    text-color: #ffffff;
}}

element-icon {{ size: 1.35em; }}
element-text {{ vertical-align: 0.5; }}
""")

add("usr/local/bin/himal-launcher", r"""#!/bin/sh
# Himal Launcher - app search, windows, files, and power controls.
# Build by Samir Puri
THEME=/etc/xdg/rofi/himal.rasi

case "${1:-}" in
    "")
        exec rofi -show combi -theme "$THEME" -combi-modi "window,drun,run"
        ;;
    apps)     exec rofi -show drun -theme "$THEME" ;;
    windows)  exec rofi -show window -theme "$THEME" ;;
    files)    exec rofi -show filebrowser -theme "$THEME" ;;
    power)
        choice=$(printf '%s\n' \
            "Lock" "Log Out" "Suspend" "Restart" "Shut Down" | \
            rofi -dmenu -theme "$THEME" -p "Power")
        case "$choice" in
            Lock)      xflock4 ;;
            "Log Out") xfce4-session-logout --logout ;;
            Suspend)   systemctl suspend ;;
            Restart)   systemctl reboot ;;
            "Shut Down") systemctl poweroff ;;
        esac
        ;;
    *)
        echo "Usage: himal-launcher [apps|windows|files|power]" >&2
        exit 1
        ;;
esac
""", 0o755)


def main():
    for path, (content, mode) in FILES.items():
        p = pathlib.Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        os.chmod(p, mode)
        print(f"  {path}")
    print(f"\n{len(FILES)} desktop-layer files written.")


if __name__ == "__main__":
    main()
