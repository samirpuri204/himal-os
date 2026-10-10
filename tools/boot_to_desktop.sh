#!/bin/sh
# Boot the Himal OS arm64 ISO through GRUB to the live desktop, headlessly.
#
# The GRUB menu waits for a keypress, and -display none gives no keyboard, so we
# drive it via the QEMU monitor's sendkey. That's what the previous run lacked.
set -u

QEMU=/opt/homebrew/bin/qemu-system-aarch64
ISO=/Users/samir/Downloads/himal-os-debian/dist/Himal-OS-13-arm64-xfce.iso
FW=/opt/homebrew/share/qemu/edk2-aarch64-code.fd
OUT=/Users/samir/Downloads/himal-os-debian/desktoptest
SOCK=$OUT/monitor.sock
FIFO=$OUT/cmd.fifo

mkdir -p "$OUT"
rm -f "$SOCK" "$FIFO" "$OUT"/*.ppm "$OUT"/serial.log "$OUT"/qemu.stdout "$OUT"/monitor.out

"$QEMU" -M virt -m 2048 -smp 2 -accel hvf -cpu host \
    -bios "$FW" \
    -device virtio-gpu-pci \
    -display none \
    -cdrom "$ISO" \
    -monitor unix:"$SOCK",server,nowait \
    -serial "file:$OUT/serial.log" \
    -no-reboot \
    >"$OUT/qemu.stdout" 2>&1 &
QPID=$!
cleanup() { kill "$QPID" 2>/dev/null; wait "$QPID" 2>/dev/null; }
trap cleanup EXIT

for _ in $(seq 1 40); do [ -S "$SOCK" ] && break; sleep 0.5; done
mkfifo "$FIFO"
nc -U "$SOCK" <"$FIFO" >"$OUT/monitor.out" 2>&1 &
NCPID=$!
exec 3>"$FIFO"
mon() { printf '%s\n' "$1" >&3; sleep 0.4; }

echo "--- waiting for the GRUB menu ---"
sleep 22
mon "screendump $OUT/g_grub.ppm"
echo "  grub menu captured"

echo "--- pressing Enter to boot the highlighted entry ---"
mon "sendkey ret"
mon "sendkey ret"

echo "--- capturing boot progress ---"
cum=22
for d in 10 15 20 25 30 40 50; do
    sleep "$d"; cum=$((cum + d))
    if ! kill -0 "$QPID" 2>/dev/null; then echo "  guest exited before t=${cum}s"; break; fi
    mon "screendump $OUT/g_${cum}.ppm"
    echo "  t=${cum}s captured"
done

echo "quit" >&3 2>/dev/null
exec 3>&- 2>/dev/null
sleep 1
kill "$NCPID" 2>/dev/null

echo
echo "=== frames ==="
for f in "$OUT"/*.ppm; do
    [ -f "$f" ] || continue
    printf "  %-16s %10s bytes  %s\n" "$(basename "$f")" "$(stat -f%z "$f")" "$(shasum -a 256 "$f" | cut -c1-16)"
done
echo
echo "=== distinct screens: $(shasum -a 256 "$OUT"/*.ppm 2>/dev/null | awk '{print substr($1,1,16)}' | sort -u | wc -l | tr -d ' ') ==="
echo
echo "=== serial (tail) ==="
[ -s "$OUT/serial.log" ] && tail -c 1500 "$OUT/serial.log" || echo "(empty)"
