#!/usr/bin/env python3
"""Himal OS applications, part 2: System Dashboard, Security Center,
Recovery System, Universal App Hub.

Credit: Build by Samir Puri
"""
import os
import pathlib

ROOT = pathlib.Path("config/includes.chroot")
BIN = ROOT / "usr/local/bin"
FILES = {}

HEAD = '''#!/usr/bin/env python3
"""%s — Build by Samir Puri"""
import os
import sys
sys.path.insert(0, "/usr/local/lib")
from himal import ui

PREV = {}


def build():
'''

FOOT = '''

if __name__ == "__main__":
    ui.run_app(build)
'''


def add(path, content):
    FILES[str(path)] = content


# ------------------------------------------------------------------ Dashboard
add(BIN / "himal-dashboard", HEAD % "Himal System Dashboard" + r'''    w, box = ui.win("Himal System Dashboard", width=660, height=600)

    def cpu_pct():
        try:
            with open("/proc/stat") as f:
                parts = [float(x) for x in f.readline().split()[1:]]
        except Exception:
            return 0.0
        idle, total = parts[3] + parts[4], sum(parts)
        p = PREV.get("cpu")
        PREV["cpu"] = (idle, total)
        if not p:
            return 0.0
        di, dt = idle - p[0], total - p[1]
        return 0.0 if dt <= 0 else max(0.0, min(100.0, 100.0 * (1 - di / dt)))

    def mem():
        info = {}
        try:
            for line in open("/proc/meminfo"):
                k, v = line.split(":", 1)
                info[k] = float(v.strip().split()[0])
        except Exception:
            pass
        total = info.get("MemTotal", 1) / 1048576.0
        avail = info.get("MemAvailable", 0) / 1048576.0
        return max(0.0, total - avail), total

    def disk():
        try:
            st = os.statvfs("/")
            used = (st.f_blocks - st.f_bfree) * st.f_frsize
            tot = st.f_blocks * st.f_frsize
            return used / 1073741824.0, tot / 1073741824.0
        except Exception:
            return 0.0, 1.0

    def net():
        rx = tx = 0
        try:
            for n in os.listdir("/sys/class/net"):
                if n == "lo":
                    continue
                rx += int(open("/sys/class/net/%s/statistics/rx_bytes" % n).read())
                tx += int(open("/sys/class/net/%s/statistics/tx_bytes" % n).read())
        except Exception:
            pass
        p = PREV.get("net")
        PREV["net"] = (rx, tx)
        if not p:
            return 0.0, 0.0
        return (rx - p[0]) / 131072.0, (tx - p[1]) / 131072.0   # Mbit/s, per 1s tick

    # Overview
    ov = ui.Gtk.Box(orientation=ui.Gtk.Orientation.HORIZONTAL, spacing=10)
    cards = {}
    for key, title in (("cpu", "CPU"), ("ram", "RAM"), ("disk", "Disk")):
        c, g = ui.card(title)
        val = ui.Gtk.Label(label="—", xalign=0)
        val.get_style_context().add_class("big-value")
        g.pack_start(val, False, False, 0)
        bar = ui.Gtk.LevelBar()
        bar.set_min_value(0); bar.set_max_value(100)
        g.pack_start(bar, False, False, 0)
        cards[key] = (val, bar)
        ov.pack_start(c, True, True, 0)

    cn, gn = ui.card("Network", "Live throughput")
    dval = ui.Gtk.Label(label="—", xalign=0)
    dval.get_style_context().add_class("big-value")
    gn.pack_start(dval, False, False, 0)
    cn2, gn2 = ui.card("System Information")
    info_lbl = ui.Gtk.Label(label="loading...", xalign=0)
    gn2.pack_start(info_lbl, False, False, 0)

    def tick():
        p = cpu_pct(); mu, mt = mem(); du, dt = disk(); rx, tx = net()
        cards["cpu"][0].set_text("%.0f%%" % p); cards["cpu"][1].set_value(p)
        cards["ram"][0].set_text("%.1f / %.1f GB" % (mu, mt))
        cards["ram"][1].set_value(100.0 * mu / max(mt, 0.001))
        cards["disk"][0].set_text("%.1f / %.1f GB" % (du, dt))
        cards["disk"][1].set_value(100.0 * du / max(dt, 0.001))
        dval.set_text("down %.1f Mbit/s    up %.1f Mbit/s" % (rx, tx))
        return True

    overview = ui.Gtk.Box(orientation=ui.Gtk.Orientation.VERTICAL, spacing=10)
    overview.pack_start(ov, False, False, 0)
    overview.pack_start(cn, False, False, 0)
    overview.pack_start(cn2, False, False, 0)
    overview.pack_start(ui.credit_line(), False, False, 0)

    # System info tab
    sysb = ui.Gtk.Box(orientation=ui.Gtk.Orientation.VERTICAL, spacing=10)
    cs, gs = ui.card("System Information")
    for label, cmd in [("Operating System", "grep -m1 PRETTY_NAME /etc/os-release | cut -d= -f2 | tr -d '\\\"'"),
                       ("Kernel", "uname -r"),
                       ("Architecture", "uname -m"),
                       ("Hostname", "cat /etc/hostname"),
                       ("Desktop", "xfconf-query -c xfce4-desktop -p /backdrop/screen0/monitor0/workspace0/last-image 2>/dev/null | sed 's#.*/##'"),
                       ("Uptime", "uptime -p | sed 's/up //'"),
                       ("Processor", "grep -m1 'model name' /proc/cpuinfo | cut -d: -f2 | sed 's/^ //'"),
                       ("Memory", "grep MemTotal /proc/meminfo | awk '{printf \\\"%.0f GB\\\", $2/1048576}'")]:
        gs.pack_start(ui.row(label, ui.Gtk.Label(label=ui.sh(cmd) or "—", xalign=1)), False, False, 0)
    sysb.pack_start(cs, False, False, 0)

    # Storage
    stb = ui.Gtk.Box(orientation=ui.Gtk.Orientation.VERTICAL, spacing=10)
    cd, gd = ui.card("Storage")
    for line in (ui.sh("df -h -x tmpfs -x devtmpfs -x squashfs 2>/dev/null") or "").splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 6:
            gd.pack_start(ui.row(parts[5], ui.Gtk.Label(label="%s / %s (%s)" % (parts[2], parts[1], parts[4]), xalign=1)), False, False, 0)
    stb.pack_start(cd, False, False, 0)

    # Processes
    pb = ui.Gtk.Box(orientation=ui.Gtk.Orientation.VERTICAL, spacing=10)
    cp, gp = ui.card("Top Processes", "Sorted by CPU")
    for line in (ui.sh("ps -eo comm,pcpu,pmem --sort=-pcpu 2>/dev/null | head -12") or "").splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 3:
            gp.pack_start(ui.row(parts[0], ui.Gtk.Label(label="%s%% cpu  %s%% mem" % (parts[1], parts[2]), xalign=1)), False, False, 0)
    pb.pack_start(cp, False, False, 0)

    # Updates
    ub = ui.Gtk.Box(orientation=ui.Gtk.Orientation.VERTICAL, spacing=10)
    cu, gu = ui.card("System Updates")
    n = len([l for l in (ui.sh("apt list --upgradable 2>/dev/null") or "").splitlines() if "/" in l])
    gu.pack_start(ui.row("Available updates", ui.Gtk.Label(label=str(n), xalign=1)), False, False, 0)
    gu.pack_start(ui.button("Open Software Updater", lambda: ui.sh(
        "xfce4-terminal -e 'sh -c \"sudo apt update && sudo apt full-upgrade -y; exec sh\"' &", timeout=3),
        suggested=True), False, False, 0)
    ub.pack_start(cu, False, False, 0)

    cont, _st = ui.stack([("Overview", ui.scroller(overview)), ("System info", ui.scroller(sysb)),
                          ("Storage", ui.scroller(stb)), ("Processes", ui.scroller(pb)),
                          ("Updates", ui.scroller(ub))])
    box.pack_start(cont, True, True, 0)

    def fill_info():
        osname = ui.sh("grep -m1 PRETTY_NAME /etc/os-release | cut -d= -f2 | tr -d '\\\"'")
        info_lbl.set_text("\\n".join([
            osname or "Himal OS",
            "Kernel %s" % (ui.sh("uname -r") or "?"),
            "Uptime %s" % (ui.sh("uptime -p | sed 's/up //'") or "?"),
            "Desktop Xfce (Himal Edition)",
            "Build by Samir Puri",
        ]))
        return False

    tick()
    fill_info()
    ui.GLib.timeout_add(1500, tick)
    return w
''' + FOOT)


# -------------------------------------------------------------- Security Center
add(BIN / "himal-security", HEAD % "Himal Security Center" + r'''    w, box = ui.win("Himal Security Center", width=560, height=620)

    def check_firewall():
        out = ui.sh("ufw status 2>/dev/null | head -1")
        return ("active" in out.lower()), (out or "ufw not available")

    def check_updates():
        n = len([l for l in (ui.sh("apt list --upgradable 2>/dev/null") or "").splitlines() if "/" in l])
        return (n == 0), ("%d updates pending" % n)

    def check_ports():
        risky = []
        for line in (ui.sh("ss -tulnH 2>/dev/null") or "").splitlines():
            for p in (":23 ", ":21 ", ":3306", ":5432", ":27017", ":111 "):
                if p in line:
                    risky.append(p.strip())
        return (not risky), ("%d risky ports open" % len(risky) if risky else "no open risky ports")

    def check_ssh():
        out = ui.sh("grep -Ei '^\\s*PermitRootLogin\\s+yes' /etc/ssh/sshd_config 2>/dev/null")
        running = ui.sh_ok("systemctl is-active ssh 2>/dev/null")
        if out:
            return False, "root login is permitted"
        return True, ("ssh active, hardened" if running else "ssh not exposed")

    def check_fail2ban():
        return ui.sh_ok("systemctl is-active fail2ban 2>/dev/null"), \
               ("fail2ban running" if ui.sh_ok("systemctl is-active fail2ban 2>/dev/null") else "fail2ban inactive")

    status_card = ui.Gtk.Box(orientation=ui.Gtk.Orientation.VERTICAL, spacing=10)

    def scan(btn=None):
        for ch in status_card.get_children():
            status_card.remove(ch)
        results = [("Firewall", check_firewall()), ("Updates", check_updates()),
                   ("Ports", check_ports()), ("SSH", check_ssh()), ("Intrusion prevention", check_fail2ban())]
        bad = sum(1 for _n, (ok, _d) in results if not ok)
        c, g = ui.card("Security Status")
        head = ui.Gtk.Label(label=("Your system is secure" if bad == 0 else "%d issue(s) found"), xalign=0)
        head.get_style_context().add_class("big-value")
        g.pack_start(head, False, False, 0)
        sub = ui.Gtk.Label(label="Last checked: %s" % (ui.sh("date '+%d %b %Y, %H:%M'") or ""), xalign=0)
        sub.get_style_context().add_class("card-sub")
        g.pack_start(sub, False, False, 0)
        for name, (ok, desc) in results:
            mark = "OK" if ok else "CHECK"
            g.pack_start(ui.row("%s  %s" % (mark, name),
                                ui.Gtk.Label(label=desc, xalign=1)), False, False, 0)
        status_card.pack_start(c, False, False, 0)
        status_card.pack_start(ui.button("Run Full Security Scan", lambda: scan(), suggested=True), False, False, 0)
        status_card.show_all()

    sb = ui.Gtk.Box(orientation=ui.Gtk.Orientation.VERTICAL, spacing=10)
    scan()
    sb.pack_start(status_card, False, False, 0)

    cf, gf = ui.card("Firewall")
    gf.pack_start(ui.row("Enable firewall", ui.switch(
        check_firewall()[0], lambda v: ui.sh("pkexec ufw %s 2>/dev/null || true" % ("enable" if v else "disable")))),
        False, False, 0)
    for rule in (ui.sh("ufw status numbered 2>/dev/null") or "").splitlines()[1:6]:
        gf.pack_start(ui.Gtk.Label(label=rule, xalign=0), False, False, 0)
    sb.pack_start(cf, False, False, 0)

    cl, gl = ui.card("Logs", "Recent authentication events")
    for line in (ui.sh("journalctl -u ssh -n 8 --no-pager 2>/dev/null || tail -8 /var/log/auth.log 2>/dev/null") or "no log access").splitlines()[:8]:
        lab = ui.Gtk.Label(label=line[:110], xalign=0)
        lab.get_style_context().add_class("card-sub")
        gl.pack_start(lab, False, False, 0)
    sb.pack_start(cl, False, False, 0)
    sb.pack_start(ui.credit_line(), False, False, 0)

    box.pack_start(ui.scroller(sb), True, True, 0)
    return w
''' + FOOT)


# ------------------------------------------------------------- Recovery System
add(BIN / "himal-recovery", HEAD % "Himal Recovery System" + r'''    w, box = ui.win("Himal Recovery System", width=580, height=600)

    def confirm(msg, action):
        d = ui.Gtk.MessageDialog(parent=w, flags=0, type=ui.Gtk.MessageType.WARNING,
                                 buttons=ui.Gtk.ButtonsType.OK_CANCEL, text=msg)
        d.format_secondary_text("This will make changes to your system. Continue?")
        if d.run() == ui.Gtk.ResponseType.OK:
            action()
        d.destroy()

    # Snapshots
    snap = ui.Gtk.Box(orientation=ui.Gtk.Orientation.VERTICAL, spacing=10)
    cs, gs = ui.card("System Snapshots", "Provided by Timeshift")
    gs.pack_start(ui.button("Create a Snapshot", lambda: confirm(
        "Create a system snapshot now?",
        lambda: ui.sh("pkexec timeshift --create --comments 'Himal OS manual snapshot' 2>/dev/null || true", timeout=300)),
        suggested=True), False, False, 0)
    listing = ui.Gtk.Box(orientation=ui.Gtk.Orientation.VERTICAL, spacing=6)
    for line in (ui.sh("timeshift --list 2>/dev/null | grep -E '^[0-9]' | head -10") or "").splitlines():
        parts = line.split()
        if len(parts) >= 3:
            listing.pack_start(ui.row(parts[1] if len(parts) > 1 else line[:20],
                                      ui.button("Restore", lambda: confirm(
                                          "Restore this snapshot? Files changed since it was taken will be reverted.",
                                          lambda: ui.sh("pkexec timeshift --restore --snapshot '%s' --yes 2>/dev/null || true"
                                                        % parts[1], timeout=900)))),
                               False, False, 0)
    if not listing.get_children():
        lab = ui.Gtk.Label(label="No snapshots yet. Create one before your next update.", xalign=0)
        lab.get_style_context().add_class("card-sub")
        listing.pack_start(lab, False, False, 0)
    gs.pack_start(listing, False, False, 0)
    snap.pack_start(cs, False, False, 0)

    # Guided repair
    rep = ui.Gtk.Box(orientation=ui.Gtk.Orientation.VERTICAL, spacing=10)
    cr, gr = ui.card("Guided Repair", "Safe, reversible fixes for common breakage")
    fixes = [
        ("Broken updates", "Finish interrupted package operations",
         "sudo dpkg --configure -a && sudo apt -f install -y"),
        ("Package errors", "Repair a damaged package database",
         "sudo apt --fix-broken install -y && sudo apt clean"),
        ("Networking problems", "Restart the network stack",
         "sudo systemctl restart NetworkManager"),
        ("Display configuration", "Reset the desktop and display settings",
         "xfconf-query -c xfwm4 -p /general/theme -s Arc-Darker"),
        ("Desktop panels", "Restore the default Himal panels",
         "himal-layout mac"),
    ]
    for title, desc, cmd in fixes:
        gr.pack_start(ui.row(title, ui.button("Repair", lambda c=cmd, t=title: confirm(
            "Run repair: %s?" % t,
            lambda: ui.sh("xfce4-terminal -e 'sh -c \"%s; echo; echo Done. Press enter.; read x\"' &" % cmd, timeout=3))),
            desc), False, False, 0)
    rep.pack_start(cr, False, False, 0)

    cl, gl = ui.card("Live Rescue")
    gl.pack_start(ui.row("System log", ui.button("Open", lambda: ui.sh("xfce4-terminal -e 'sh -c \"journalctl -b -p err; exec sh\"' &", timeout=3))), False, False, 0)
    gl.pack_start(ui.row("Disk health", ui.button("Open", lambda: ui.sh("xfce4-terminal -e 'sh -c \"sudo smartctl -a /dev/sda 2>/dev/null || lsblk; exec sh\"' &", timeout=3))), False, False, 0)
    rep.pack_start(cl, False, False, 0)
    rep.pack_start(ui.credit_line(), False, False, 0)

    cont, _st = ui.stack([("Snapshots", ui.scroller(snap)), ("Repair", ui.scroller(rep))])
    box.pack_start(cont, True, True, 0)
    return w
''' + FOOT)


# ------------------------------------------------------------------ App Hub
add(BIN / "himal-apphub", HEAD % "Himal Universal App Hub" + r'''    w, box = ui.win("Himal Universal App Hub", width=620, height=620)

    results = ui.Gtk.Box(orientation=ui.Gtk.Orientation.VERTICAL, spacing=6)
    entry = ui.Gtk.SearchEntry()
    entry.set_placeholder_text("Search applications...")

    source = ui.dropdown(["All sources", "APT (Debian)", "Flatpak", "AppImage"], 0, lambda i: do_search(entry.get_text(), i))

    def install_apt(pkg):
        confirm = ui.Gtk.MessageDialog(parent=w, flags=0, type=ui.Gtk.MessageType.QUESTION,
                                       buttons=ui.Gtk.ButtonsType.OK_CANCEL,
                                       text="Install %s?" % pkg)
        confirm.format_secondary_text("Source: Debian APT repository (main/contrib/non-free)")
        if confirm.run() == ui.Gtk.ResponseType.OK:
            ui.sh("xfce4-terminal -e 'sh -c \"sudo apt install -y %s; echo; echo Press enter.; read x\"' &" % pkg, timeout=3)
        confirm.destroy()

    def install_flatpak(appid):
        confirm = ui.Gtk.MessageDialog(parent=w, flags=0, type=ui.Gtk.MessageType.QUESTION,
                                       buttons=ui.Gtk.ButtonsType.OK_CANCEL,
                                       text="Install %s?" % appid)
        confirm.format_secondary_text("Source: Flathub")
        if confirm.run() == ui.Gtk.ResponseType.OK:
            ui.sh("xfce4-terminal -e 'sh -c \"flatpak install -y flathub %s; echo; echo Press enter.; read x\"' &" % appid, timeout=3)
        confirm.destroy()

    def clear():
        for ch in results.get_children():
            results.remove(ch)

    def do_search(query, src=0):
        clear()
        if src in (0, 1) and len(query) >= 2:
            out = ui.sh("apt-cache search --names-only '%s' 2>/dev/null | head -14" % query.replace("'", ""))
            if out:
                h = ui.Gtk.Label(label="APT (Debian)", xalign=0)
                h.get_style_context().add_class("section")
                results.pack_start(h, False, False, 0)
            for line in out.splitlines():
                pkg, _, desc = line.partition(" - ")
                results.pack_start(ui.row(pkg, ui.button("Install", lambda p=pkg: install_apt(p)), desc[:70]),
                                   False, False, 0)
        if src in (0, 2) and len(query) >= 2:
            out = ui.sh("flatpak search --columns=application,name,description '%s' 2>/dev/null | head -10" % query.replace("'", ""))
            if out:
                h = ui.Gtk.Label(label="Flatpak (Flathub)", xalign=0)
                h.get_style_context().add_class("section")
                results.pack_start(h, False, False, 0)
            for line in out.splitlines():
                cols = line.split("\t")
                if len(cols) >= 2:
                    results.pack_start(ui.row(cols[1], ui.button("Install", lambda a=cols[0]: install_flatpak(a)),
                                              cols[2][:70] if len(cols) > 2 else ""), False, False, 0)
        if src == 3:
            h = ui.Gtk.Label(label="AppImage", xalign=0)
            h.get_style_context().add_class("section")
            results.pack_start(h, False, False, 0)
            found = ui.sh("ls ~/Applications/*.AppImage ~/.local/bin/*.AppImage 2>/dev/null | head -10")
            for f in (found or "").splitlines():
                results.pack_start(ui.row(os.path.basename(f), ui.button("Make executable", lambda p=f: ui.sh(
                    "chmod +x '%s'" % p))), False, False, 0)
            if not found:
                lab = ui.Gtk.Label(label="No AppImages found. Drop them in ~/Applications.", xalign=0)
                lab.get_style_context().add_class("card-sub")
                results.pack_start(lab, False, False, 0)
        if not results.get_children():
            lab = ui.Gtk.Label(label="Type at least two characters, or open another source tab.", xalign=0)
            lab.get_style_context().add_class("card-sub")
            results.pack_start(lab, False, False, 0)
        results.show_all()

    entry.connect("activate", lambda e: do_search(e.get_text(), source.get_active()))

    top = ui.Gtk.Box(orientation=ui.Gtk.Orientation.HORIZONTAL, spacing=8)
    top.pack_start(entry, True, True, 0)
    top.pack_start(source, False, False, 0)
    box.pack_start(top, False, False, 0)

    c, g = ui.card("Discover", "APT packages and Flatpak apps, with their source shown before install")
    g.pack_start(ui.scroller(results), True, True, 0)
    c.set_size_request(-1, 380)
    box.pack_start(c, True, True, 0)

    for line in (ui.sh("flatpak remotes 2>/dev/null") or "no flatpak remotes").splitlines()[:2]:
        lab = ui.Gtk.Label(label="remote: %s" % line, xalign=0)
        lab.get_style_context().add_class("card-sub")
        box.pack_start(lab, False, False, 0)
    box.pack_start(ui.credit_line(), False, False, 0)
    do_search("", 0)
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
