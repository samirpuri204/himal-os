#!/usr/bin/env python3
"""Himal OS applications, part 1: Control Center, Personalization Studio,
Performance Mode.

Credit: Build by Samir Puri
"""
import os
import pathlib

ROOT = pathlib.Path("config/includes.chroot")
BIN = ROOT / "usr/local/bin"
FILES = {}


def add(path, content):
    FILES[str(path)] = content


HEAD = '''#!/usr/bin/env python3
"""%s — Build by Samir Puri"""
import os
import sys
sys.path.insert(0, "/usr/local/lib")
from himal import ui


def build():
'''

FOOT = '''

if __name__ == "__main__":
    ui.run_app(build)
'''


# ------------------------------------------------------------- Control Center
add(BIN / "himal-control-center", HEAD % "Himal Control Center" + r'''    w, box = ui.win("Himal Control Center", width=440, height=600)

    def wifi_state():
        return ui.sh("nmcli -t -f WIFI general | head -1") == "enabled"

    def bt_state():
        return ui.sh("rfkill list bluetooth 2>/dev/null | grep -c 'Soft blocked: no'") != "0"

    def perf_state():
        p = ui.sh("powerprofilesctl get 2>/dev/null") or "balanced"
        return {"power-saver": 0, "balanced": 1, "performance": 2}.get(p, 1)

    def dark_state():
        t = ui.sh("xfconf-query -c xsettings -p /Net/ThemeName 2>/dev/null")
        return "Darker" in t or "Dark" in t

    # ---- Quick Settings ----
    quick = ui.Gtk.Box(orientation=ui.Gtk.Orientation.VERTICAL, spacing=10)

    c1, g1 = ui.card("Network")
    ssid = ui.sh("nmcli -t -f NAME connection show --active 2>/dev/null | head -1") or "not connected"
    g1.pack_start(ui.row("Wi-Fi", ui.switch(wifi_state(), lambda v: ui.sh(
        "nmcli radio wifi %s" % ("on" if v else "off"))), ssid), False, False, 0)
    g1.pack_start(ui.row("Bluetooth", ui.switch(bt_state(), lambda v: ui.sh(
        "rfkill %s bluetooth" % ("unblock" if v else "block")))), False, False, 0)
    quick.pack_start(c1, False, False, 0)

    c2, g2 = ui.card("Appearance")
    g2.pack_start(ui.row("Dark Mode", ui.switch(dark_state(), lambda v: (
        ui.sh("xfconf-query -c xsettings -p /Net/ThemeName -s %s" % ("Arc-Darker" if v else "Arc")),
        ui.sh("xfconf-query -c xsettings -p /Net/IconThemeName -s %s" % ("Papirus-Dark" if v else "Papirus"))
    ))), False, False, 0)
    g2.pack_start(ui.row("Night Light", ui.switch(
        ui.sh_ok("pgrep -x gammastep"), lambda v: ui.sh(
            "(pkill -x gammastep || true); %s" % ("(gammastep -O 3800 >/dev/null 2>&1 &)" if v else "true")
        )), "Warm screen after dark"), False, False, 0)
    quick.pack_start(c2, False, False, 0)

    c3, g3 = ui.card("Sound and Display")
    bright = int(ui.sh("brightnessctl get 2>/dev/null") or "50")
    g3.pack_start(ui.row("Brightness", ui.slider(bright, 1, 100, lambda v: ui.sh(
        "brightnessctl set %d%% 2>/dev/null" % int(v)))), False, False, 0)
    vol = int(ui.sh("pactl get-sink-volume @DEFAULT_SINK@ 2>/dev/null | grep -o '[0-9]*%' | head -1 | tr -d '%'") or "50")
    g3.pack_start(ui.row("Volume", ui.slider(vol, 0, 150, lambda v: ui.sh(
        "pactl set-sink-volume @DEFAULT_SINK@ %d%%" % int(v)))), False, False, 0)
    g3.pack_start(ui.row("Sound Settings", ui.button("Open", lambda: ui.sh(
        "pavucontrol &", timeout=3), suggested=True)), False, False, 0)
    quick.pack_start(c3, False, False, 0)

    c4, g4 = ui.card("Power")
    bat = ui.sh("cat /sys/class/power_supply/BAT*/capacity 2>/dev/null | head -1")
    g4.pack_start(ui.row("Performance", ui.dropdown(
        ["Eco", "Balanced", "Performance"], perf_state(), lambda i: ui.sh(
            "powerprofilesctl set %s 2>/dev/null" % ["power-saver", "balanced", "performance"][i])),
        ("Battery %s%%" % bat) if bat else "on AC power"), False, False, 0)
    quick.pack_start(c4, False, False, 0)

    # ---- All Settings ----
    alls = ui.Gtk.Box(orientation=ui.Gtk.Orientation.VERTICAL, spacing=10)
    ca, ga = ui.card("Himal Tools")
    for label, cmd in [
        ("Personalization Studio", "himal-studio"),
        ("System Dashboard", "himal-dashboard"),
        ("Security Center", "himal-security"),
        ("Performance Mode", "himal-performance"),
        ("Recovery System", "himal-recovery"),
        ("Universal App Hub", "himal-apphub"),
    ]:
        ga.pack_start(ui.row(label, ui.button("Open", lambda c=cmd: ui.sh("%s &" % c, timeout=3))),
                      False, False, 0)
    alls.pack_start(ca, False, False, 0)

    cb, gb = ui.card("System Settings")
    for label, cmd in [
        ("Display", "xfce4-display-settings"),
        ("Keyboard", "xfce4-keyboard-settings"),
        ("Power Manager", "xfce4-power-manager-settings"),
        ("Network Connections", "nm-connection-editor"),
        ("Bluetooth Devices", "blueman-manager"),
    ]:
        gb.pack_start(ui.row(label, ui.button("Open", lambda c=cmd: ui.sh("%s &" % c, timeout=3))),
                      False, False, 0)
    alls.pack_start(cb, False, False, 0)
    box.pack_start(ui.credit_line(), False, False, 0)

    container, _st = ui.stack([("Quick Settings", ui.scroller(quick)),
                               ("All Settings", ui.scroller(alls))])
    box.pack_start(container, True, True, 0)
    return w
''' + FOOT)


# ------------------------------------------------------- Personalization Studio
add(BIN / "himal-studio", HEAD % "Himal Personalization Studio" + r'''    w, box = ui.win("Himal Personalization Studio", width=560, height=600)
    WALL_DIR = "/usr/share/backgrounds/himal"

    # Themes
    themes = ui.Gtk.Box(orientation=ui.Gtk.Orientation.VERTICAL, spacing=10)
    ct, gt = ui.card("Appearance")
    dark = "Darker" in ui.sh("xfconf-query -c xsettings -p /Net/ThemeName 2>/dev/null")
    gt.pack_start(ui.row("Theme", ui.dropdown(
        ["Arc (Himal)", "Arc-Darker (Himal)", "Greybird", "Numix"],
        [ "Arc", "Arc-Darker", "Greybird", "Numix" ].index(
            ui.sh("xfconf-query -c xsettings -p /Net/ThemeName 2>/dev/null") or "Arc"),
        lambda i: ui.sh("xfconf-query -c xsettings -p /Net/ThemeName -s %s"
                        % ["Arc", "Arc-Darker", "Greybird", "Numix"][i]))), False, False, 0)
    gt.pack_start(ui.row("Icon Pack", ui.dropdown(
        ["Papirus", "Papirus-Dark", "Numix", "elementary Xfce"],
        ["Papirus", "Papirus-Dark", "Numix", "elementary-xfce"].index(
            ui.sh("xfconf-query -c xsettings -p /Net/IconThemeName 2>/dev/null") or "Papirus"),
        lambda i: ui.sh("xfconf-query -c xsettings -p /Net/IconThemeName -s %s"
                        % ["Papirus", "Papirus-Dark", "Numix", "elementary-xfce"][i]))), False, False, 0)
    gt.pack_start(ui.row("Use Nepali Fonts", ui.switch(
        "Noto Sans Devanagari" in ui.sh("xfconf-query -c xsettings -p /Gtk/FontName 2>/dev/null"),
        lambda v: ui.sh("xfconf-query -c xsettings -p /Gtk/FontName -s '%s'"
                        % ("Noto Sans Devanagari 10" if v else "Noto Sans 10")))),
        False, False, 0)
    themes.pack_start(ct, False, False, 0)

    ca, ga = ui.card("Accent Colour")
    acc = ui.sh("nmcli --version >/dev/null 2>&1 && echo ok")  # no-op keeps layout stable
    acc_row = ui.Gtk.Box(orientation=ui.Gtk.Orientation.HORIZONTAL, spacing=8)
    accents = [("#1698D2", "Himal Blue"), ("#2ECC71", "Everest Green"),
               ("#E0A24A", "Amber"), ("#8E5CD9", "Rhododendron"),
               ("#E05A6A", "Crimson"), ("#3AB0A2", "Teal")]
    for colour, name in accents:
        b = ui.Gtk.Button()
        b.set_tooltip_text(name)
        css = ui.Gtk.CssProvider()
        css.load_from_data(("button{background-image:none;background-color:%s;"
                            "min-width:26px;min-height:26px;border-radius:13px;}" % colour).encode())
        b.get_style_context().add_provider(css, ui.Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        b.connect("clicked", lambda _w, c=colour: ui.sh(
            "sed -i 's/@himal_accent .*/@himal_accent %s;/' /etc/gtk-3.0/gtk.css 2>/dev/null || true" % c))
        acc_row.pack_start(b, False, False, 0)
    ga.pack_start(acc_row, False, False, 0)
    themes.pack_start(ca, False, False, 0)

    # Wallpapers
    walls = ui.Gtk.Box(orientation=ui.Gtk.Orientation.VERTICAL, spacing=10)
    cw, gw = ui.card("Wallpapers", "Click a wallpaper to apply it")
    for f in sorted(os.listdir(WALL_DIR)) if os.path.isdir(WALL_DIR) else []:
        if not f.endswith(".png") or "1920x1080" in f:
            continue
        name = f.replace("himal-wallpaper-", "").replace(".png", "").title()
        gw.pack_start(ui.row(name, ui.button("Apply", lambda p=os.path.join(WALL_DIR, f):
                                             ui.sh("himal wallpaper %s" % p.split("himal-wallpaper-")[-1][:-4]),
                                             suggested=True)), False, False, 0)
    walls.pack_start(cw, False, False, 0)

    # Layouts
    lays = ui.Gtk.Box(orientation=ui.Gtk.Orientation.VERTICAL, spacing=10)
    cl, gl = ui.card("Desktop Layout", "Switches live — no restart needed")
    gl.pack_start(ui.row("macOS Style", ui.button("Apply", lambda: ui.sh(
        "himal-layout mac"), suggested=True), "Top bar with a floating dock"), False, False, 0)
    gl.pack_start(ui.row("Windows Style", ui.button("Apply", lambda: ui.sh(
        "himal-layout windows")), "Bottom taskbar with a Start menu"), False, False, 0)
    gl.pack_start(ui.row("Minimal Style", ui.button("Apply", lambda: ui.sh(
        "himal-layout mac; pkill -x plank 2>/dev/null || true")), "Top bar only, no dock"), False, False, 0)
    lays.pack_start(cl, False, False, 0)
    lays.pack_start(ui.credit_line(), False, False, 0)

    container, _st = ui.stack([("Themes", ui.scroller(themes)),
                               ("Wallpapers", ui.scroller(walls)),
                               ("Layouts", ui.scroller(lays))])
    box.pack_start(container, True, True, 0)
    return w
''' + FOOT)


# ------------------------------------------------------------ Performance Mode
add(BIN / "himal-performance", HEAD % "Himal Performance Mode" + r'''    w, box = ui.win("Himal Performance Mode", width=520, height=560)

    current = ui.sh("powerprofilesctl get 2>/dev/null") or "balanced"
    modes = [
        ("Eco", "power-saver", "Save power for longer battery life"),
        ("Balanced", "balanced", "Best balance for daily use"),
        ("Performance", "performance", "Maximum performance for heavy tasks"),
    ]

    c, g = ui.card("Performance Profile", "Applied through power-profiles-daemon — real hardware tuning")
    rowbox = ui.Gtk.Box(orientation=ui.Gtk.Orientation.HORIZONTAL, spacing=10)
    for label, key, desc in modes:
        b = ui.Gtk.Button(label=label)
        b.set_size_request(140, 84)
        if key == current:
            b.get_style_context().add_class("suggested-action")
        b.set_tooltip_text(desc)
        b.connect("clicked", lambda _w, k=key, l=label: (
            ui.sh("powerprofilesctl set %s 2>/dev/null" % k),
            ui.sh("notify-send 'Himal OS' 'Performance set to %s'" % l)))
        rowbox.pack_start(b, True, True, 0)
    g.pack_start(rowbox, False, False, 0)
    box.pack_start(c, False, False, 0)

    c2, g2 = ui.card("Hardware Tuning")
    gov = ui.sh("cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null") or "n/a"
    g2.pack_start(ui.row("CPU Performance Scaling",
                         ui.dropdown(["Power Save", "Balanced", "Performance"],
                                     {"powersave": 0, "schedutil": 1, "performance": 2}.get(gov, 1),
                                     lambda i: ui.sh("cpupower frequency-set -g %s 2>/dev/null || true"
                                                     % ["powersave", "schedutil", "performance"][i])),
                         gov), False, False, 0)
    g2.pack_start(ui.row("Power Management", ui.switch(
        ui.sh_ok("systemctl is-enabled power-profiles-daemon 2>/dev/null"),
        lambda v: ui.sh("systemctl %s power-profiles-daemon 2>/dev/null || true"
                        % ("enable" if v else "disable")))), False, False, 0)
    g2.pack_start(ui.row("Auto Suspend", ui.switch(
        "1" in ui.sh("xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/inactivity-on-ac 2>/dev/null | tail -1"),
        lambda v: ui.sh("xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/inactivity-on-ac "
                        "-n -t uint -s %d 2>/dev/null || true" % (14 if v else 0)))),
        False, False, 0)
    g2.pack_start(ui.row("Disk Optimization", ui.button("Run fstrim", lambda: ui.sh(
        "pkexec fstrim -av 2>/dev/null || true")), "Trim unmapped blocks on SSDs"), False, False, 0)
    box.pack_start(c2, False, False, 0)

    box.pack_start(ui.credit_line(), False, False, 0)
    return w
''' + FOOT)


def main():
    for path, content in FILES.items():
        p = pathlib.Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        os.chmod(p, 0o755)
        print(f"  {path}")

    import py_compile
    print()
    for path in FILES:
        try:
            py_compile.compile(path, doraise=True)
            print(f"  [OK]   {os.path.basename(path)}")
        except Exception as e:
            print(f"  [FAIL] {os.path.basename(path)}: {e}")


if __name__ == "__main__":
    main()
