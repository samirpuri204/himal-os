#!/bin/sh
# Boot through GRUB to the live desktop.
#
# The shipped grub.cfg has no 'set timeout', so GRUB waits for input forever.
# On -M virt the arm64 UEFI console takes input from the SERIAL port, not from
# QEMU's sendkey, so we drive it by writing a carriage return into a
# bidirectional serial socket.
set -u

QEMU=/opt/homebrew/bin/qemu-system-aarch64
ISO=/Users/samir/Downloads/himal-os-debian/dist/Himal-OS-13-arm64-xfce.iso
FW=/opt/homebrew/share/qemu/edk2-aarch64-code.fd
OUT=/Users/samir/Downloads/himal-os-debian/desktoptest2
SOCK=$OUT/monitor.sock
FIFO=$OUT/cmd.fifo
SER=$OUT/ser.sock
SERFIFO=$OUT/ser.fifo

mkdir -p "$OUT"
rm -f "$SOCK" "$FIFO" "$SER" "$SERFIFO" "$OUT"/*.ppm "$OUT"/qemu.stdout "$OUT"/monitor.out

"$QEMU" -M virt -m 2048 -smp 2 -accel hvf -cpu host \
    -bios "$FW" \
    -device virtio-gpu-pci \
    -display none \
    -cdrom "$ISO" \
    -monitor unix:"$SOCK",server,nowait \
    -serial unix:"$SER",server,nowait \
    -no-reboot \
    >"$OUT/qemu.stdout" 2>&1 &
QPID=$!
cleanup() { kill "$QPID" 2>/dev/null; wait "$QPID" 2>/dev/null; }
trap cleanup EXIT

for _ in $(seq 1 40); do [ -S "$SOCK" ] && break; sleep 0.5; done
mkfifo "$FIFO"; nc -U "$SOCK" <"$FIFO" >"$OUT/monitor.out" 2>&1 & NCPID=$!
exec 3>"$FIFO"
mon() { printf '%s\n' "$1" >&3; sleep 0.4; }

# bidirectional serial: read into a log, keep the write end open
for _ in $(seq 1 40); do [ -S "$SER" ] && break; sleep 0.5; done
mkfifo "$SERFIFO"
nc -U "$SER" <"$SERFIFO" >"$OUT/serial.log" 2>&1 & SERPID=$!
exec 4>"$SERFIFO"

echo "--- waiting for GRUB ---"
sleep 22
mon "screendump $OUT/g_grub.ppm"

echo "--- sending Enter over the serial console ---"
printf '\r' >&4
sleep 2
printf '\r' >&4
sleep 1
printf '\r' >&4

echo "--- capturing ---"
cum=22
for d in 12 15 20 25 30 40 45; do
    sleep "$d"; cum=$((cum + d))
    if ! kill -0 "$QPID" 2>/dev/null; then echo "  guest exited before t=${cum}s"; break; fi
    mon "screendump $OUT/g_${cum}.ppm"
    echo "  t=${cum}s captured"
done

echo "quit" >&3 2>/dev/null
exec 3>&- 2>/dev/null
exec 4>&- 2>/dev/null
sleep 1
kill "$NCPID" "$SERPID" 2>/dev/null

echo
echo "=== frames ==="
for f in "$OUT"/*.ppm; do
    [ -f "$f" ] || continue
    printf "  %-16s %10s bytes  %s\n" "$(basename "$f")" "$(stat -f%z "$f")" "$(shasum -a 256 "$f" | cut -c1-16)"
done
echo "=== distinct screens: $(shasum -a 256 "$OUT"/*.ppm 2>/dev/null | awk '{print substr($1,1,16)}' | sort -u | wc -l | tr -d ' ') ==="
echo
echo "=== serial log (tail) ==="
[ -s "$OUT/serial.log" ] && tail -c 1200 "$OUT/serial.log" || echo "(empty)"
