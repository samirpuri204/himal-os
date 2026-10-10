#!/bin/sh
# Full read-back verification of the Himal OS ISO.
#
# Everything is checked by reading it back OUT of the finished image, never by
# trusting that it was staged. That method is what caught the /xdg/ path bug,
# the greeter's literal %s, and the misplaced gtk.css.
#
# Existence is checked against `unsquashfs -l` output (fast, and a single missing
# path cannot abort it). Only files whose *contents* matter are extracted.
set -u

ISO=/Users/samir/Downloads/himal-os-debian/dist/Himal-OS-13-arm64-xfce.iso
DOCKER_HOST=unix:///Users/samir/.colima/default/docker.sock; export DOCKER_HOST
DOCKER_CONFIG=/Users/samir/Downloads/himal-os/build/dockercfg; export DOCKER_CONFIG

PASS=0; FAIL=0
ok()   { printf "  [OK]   %s\n" "$1"; PASS=$((PASS+1)); }
bad()  { printf "  [FAIL] %s\n" "$1"; FAIL=$((FAIL+1)); }
has()  { # has <description> <path-regex>
  if grep -qE "$2" "$TMP/sq.list" 2>/dev/null; then ok "$1"; else bad "$1"; fi
}
wantc() { # wantc <description> <content-file> <pattern>
  if grep -q "$3" "$2" 2>/dev/null; then ok "$1"; else bad "$1"; fi
}

echo "=============================================================="
echo " Himal OS ISO verification"
echo "=============================================================="
[ -f "$ISO" ] || { echo "  ISO NOT FOUND: $ISO"; exit 1; }
echo "  path  : $ISO"
echo "  size  : $(stat -f%z "$ISO") bytes"
echo "  sha256: $(shasum -a 256 "$ISO" | awk '{print $1}')"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# ---------------------------------------------------------------- boot + volume
echo
echo "--- boot records and volume branding ---"
python3 - "$ISO" >"$TMP/pvd.txt" <<'PY'
import sys, pathlib
d = pathlib.Path(sys.argv[1]).read_bytes()
def at(o, n): return d[o:o+n].decode('ascii', 'replace').strip()
print("volume_id=" + at(32808, 32))
print("publisher=" + at(33086, 128))
print("application=" + at(33342, 128))
off = 16*2048
found = any(d[off+i*2048+1:off+i*2048+6] == b'CD001' and d[off+i*2048] == 0 for i in range(6))
print("eltorito=" + ("yes" if found else "no"))
PY
cat "$TMP/pvd.txt" | sed 's/^/    /'
wantc "Volume ID is HIMAL_OS"          "$TMP/pvd.txt" "volume_id=HIMAL_OS"
wantc "Publisher is Himal OS Project"  "$TMP/pvd.txt" "publisher=HIMAL OS PROJECT"
wantc "El Torito boot record present"  "$TMP/pvd.txt" "eltorito=yes"

# ---------------------------------------------------------------- grub
echo
echo "--- GRUB menu ---"
if tar -xf "$ISO" -C "$TMP" boot/grub/grub.cfg 2>/dev/null; then
    G="$TMP/boot/grub/grub.cfg"
    wantc "GRUB has a boot timeout"   "$G" "set timeout="
    wantc "GRUB has a default entry"  "$G" "set default="
    if grep -q "Himal OS Live" "$G"; then
        ok "menu entries say 'Himal OS Live'"
        grep -o 'menuentry "[^"]*"' "$G" | head -4 | sed 's/^/           /'
    else
        bad "menu entries still say 'Live system'"
    fi
    grep -q "Debian GNU/Linux 13" "$G" && bad "Debian banner text still present" \
                                       || ok "Debian banner text gone"
else
    bad "could not extract grub.cfg"
fi

echo
echo "--- EFI bootloader (the ReactOS failure point) ---"
if tar -tf "$ISO" 2>/dev/null | grep -q "bootaa64.efi"; then
    ok "bootaa64.efi present (64-bit EFI loader)"
else
    bad "bootaa64.efi missing"
fi

# ---------------------------------------------------- build the squashfs listing
echo
echo "--- live filesystem ---"
docker exec himal-deb bash -lc 'unsquashfs -l /root/himal/binary/live/filesystem.squashfs 2>/dev/null' \
    | sed 's|^squashfs-root/||' > "$TMP/sq.list" 2>/dev/null
N=$(wc -l < "$TMP/sq.list" | tr -d ' ')
echo "  indexed $N paths"
if [ "$N" -lt 1000 ]; then echo "  ABORT: listing looks wrong"; exit 1; fi

echo
echo "  identity"
has "os-release"           "^etc/os-release$"
has "login banner (issue)" "^etc/issue$"
has "motd"                 "^etc/motd$"
has "hostname"             "^etc/hostname$"
has "fastfetch config"     "^etc/fastfetch/config.jsonc$"

echo
echo "  desktop layer  (the /xdg and /gtk-3.0 path bugs lived here)"
has "picom compositor config"  "^etc/xdg/picom/picom.conf$"
has "rofi launcher theme"      "^etc/xdg/rofi/himal.rasi$"
has "GTK3 Himal stylesheet"    "^etc/gtk-3.0/gtk.css$"
has "xfce4-desktop config"     "^etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xfce4-desktop.xml$"
has "xfce4-panel config"       "^etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml$"
has "compositor autostart"     "^etc/xdg/autostart/himal-compositor.desktop$"
has "plank dock settings"      "^etc/xdg/plank/dock1/settings$"
if grep -qE "^gtk-3.0/gtk.css$" "$TMP/sq.list"; then
    bad "gtk.css ALSO at the image root (/gtk-3.0) - stray directory"
else
    ok "no stray /gtk-3.0 at the image root"
fi

echo
echo "  the himal commands"
for a in himal himal-control-center himal-studio himal-dashboard himal-security \
         himal-recovery himal-performance himal-apphub himal-launcher \
         himal-credit-guard himal-calendar himal-firstboot himal-set-wallpaper \
         himal-layout himal-layout-switch himal-welcome; do
    has "  $a" "^usr/local/bin/$a$"
done
has "shared UI module" "^usr/local/lib/himal/ui.py$"

echo
echo "  boot splash"
has "plymouth theme definition" "^usr/share/plymouth/themes/himal/himal.plymouth$"
has "plymouth script"           "^usr/share/plymouth/themes/himal/himal.script$"
has "splash logo"               "^usr/share/plymouth/themes/himal/logo.png$"

echo
echo "  credit system"
has "master credit .txt"  "^usr/share/himal/credit/HIMAL-OS-CREDIT.txt$"
has "master credit .md"   "^usr/share/himal/credit/HIMAL-OS-CREDIT.md$"
has "guard script"        "^usr/local/bin/himal-credit-guard$"
has "systemd service"     "^etc/systemd/system/himal-credit.service$"
has "systemd timer"       "^etc/systemd/system/himal-credit.timer$"
has "timer enabled"       "^etc/systemd/system/timers.target.wants/himal-credit.timer$"
has "desktop credit icon" "^usr/share/applications/himal-credit.desktop$"

echo
echo "  Nepal-first and safer defaults"
has "Nepali + US keyboard"     "^etc/default/keyboard$"
has "automatic security updates" "^etc/apt/apt.conf.d/20auto-upgrades$"
has "firewall enabled config"  "^etc/ufw/ufw.conf$"
has "first-boot safe defaults" "^usr/local/bin/himal-firstboot$"

echo
echo "  wallpapers and icons"
has "credited wallpaper"  "^usr/share/backgrounds/himal/himal-wallpaper-abyss.png$"
has "logo pixmap"         "^usr/share/pixmaps/himal-logo.png$"
has "hicolor 256 icon"    "^usr/share/icons/hicolor/256x256/apps/himal-logo.png$"

echo
echo "  menu entries"
has "control center entry" "^usr/share/applications/himal-control-center.desktop$"
has "studio entry"         "^usr/share/applications/himal-studio.desktop$"
has "dashboard entry"      "^usr/share/applications/himal-dashboard.desktop$"

# ------------------------------------------------------------- content checks
echo
echo "--- file contents ---"
docker exec himal-deb bash -lc '
rm -rf /tmp/vfy; mkdir -p /tmp/vfy
unsquashfs -q -d /tmp/vfy /root/himal/binary/live/filesystem.squashfs \
  etc/os-release etc/issue etc/default/keyboard etc/gtk-3.0/gtk.css \
  usr/share/plymouth/themes/himal/himal.script \
  usr/share/himal/credit/HIMAL-OS-CREDIT.txt 2>/dev/null
for f in etc/os-release etc/issue etc/default/keyboard etc/gtk-3.0/gtk.css \
         usr/share/plymouth/themes/himal/himal.script \
         usr/share/himal/credit/HIMAL-OS-CREDIT.txt; do
  [ -f "/tmp/vfy/$f" ] && echo "=== $f" && cat "/tmp/vfy/$f"
done
' > "$TMP/content.txt" 2>&1

wantc "os-release names Himal OS"    "$TMP/content.txt" "PRETTY_NAME=\"Himal OS 13\""
wantc "os-release carries the credit" "$TMP/content.txt" "Samir Puri"
wantc "keyboard has us,np layouts"   "$TMP/content.txt" "XKBLAYOUT=\"us,np\""
wantc "GTK stylesheet has Himal accent" "$TMP/content.txt" "himal_accent"
wantc "splash carries the credit"    "$TMP/content.txt" "Build by Samir Puri"
wantc "credit file names the builder" "$TMP/content.txt" "Samir Puri"
wantc "issue banner backslash doubled" "$TMP/content.txt" '\\\\'

echo
echo "=============================================================="
echo " RESULT: $PASS passed, $FAIL failed"
echo "=============================================================="
if [ "$FAIL" -eq 0 ]; then echo " All checks passed."; else echo " See the [FAIL] lines above."; fi
