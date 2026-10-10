#!/bin/sh
# Capture the Himal OS boot densely enough to actually catch the Plymouth splash.
#
# The previous run missed it: GRUB now auto-boots after 10s (the timeout fix), so
# the splash window is only a few seconds wide and my 22s / 34s samples straddled it.
# This samples every 2s from t=10s to t=44s, then coarsely for the desktop.
set -u

QEMU=/opt/homebrew/bin/qemu-system-aarch64
ISO=/Users/samir/Downloads/himal-os-debian/dist/Himal-OS-13-arm64-xfce.iso
FW=/opt/homebrew/share/qemu/edk2-aarch64-code.fd
OUT=/Users/samir/Downloads/himal-os-debian/splashtest
SOCK=$OUT/monitor.sock
FIFO=$OUT/cmd.fifo
SER=$OUT/ser.sock
SERFIFO=$OUT/ser.fifo

mkdir -p "$OUT"
rm -f "$SOCK" "$FIFO" "$SER" "$SERFIFO" "$OUT"/*.ppm "$OUT"/qemu.stdout "$OUT"/monitor.out

"$QEMU" -M virt -m 2048 -smp 2 -accel hvf -cpu host \
    -bios "$FW" \
    -device virtio-gpu-pci -display none \
    -cdrom "$ISO" \
    -monitor unix:"$SOCK",server,nowait \
    -serial unix:"$SER",server,nowait \
    -no-reboot >"$OUT/qemu.stdout" 2>&1 &
QPID=$!
cleanup() { kill "$QPID" 2>/dev/null; wait "$QPID" 2>/dev/null; }
trap cleanup EXIT

for _ in $(seq 1 40); do [ -S "$SOCK" ] && break; sleep 0.5; done
mkfifo "$FIFO"; nc -U "$SOCK" <"$FIFO" >"$OUT/monitor.out" 2>&1 & NCPID=$!
exec 3>"$FIFO"
mon() { printf '%s\n' "$1" >&3; }

for _ in $(seq 1 40); do [ -S "$SER" ] && break; sleep 0.5; done
mkfifo "$SERFIFO"; nc -U "$SER" <"$SERFIFO" >"$OUT/serial.log" 2>&1 & SERPID=$!
exec 4>"$SERFIFO"

echo "--- dense capture, every 2s from t=10s ---"
n=0
t=10
while [ "$t" -le 44 ]; do
    sleep 2; t=$((t + 2)); n=$((n + 1))
    if ! kill -0 "$QPID" 2>/dev/null; then echo "  guest exited at t=${t}s"; break; fi
    mon "screendump $OUT/b_$(printf '%02d' $t).ppm"
    mon "sendkey ret" 2>/dev/null || true      # harmless; the timeout already boots it
done
echo "  captured $n frames in the splash window"

echo "--- coarse capture for the desktop ---"
cum=44
for delta in 16 20 30 40; do
    sleep "$delta"; cum=$((cum + delta))
    if ! kill -0 "$QPID" 2>/dev/null; then break; fi
    mon "screendump $OUT/d_${cum}.ppm"
    echo "  captured d_${cum}"
done

echo "quit" >&3 2>/dev/null
exec 3>&- 2>/dev/null
exec 4>&- 2>/dev/null
sleep 1
kill "$NCPID" "$SERPID" 2>/dev/null

echo
echo "=== frames: size, distinct colours, hash ==="
python3 - "$OUT" <<'PY'
import sys, pathlib, struct
d = pathlib.Path(sys.argv[1])
for p in sorted(d.glob('*.ppm')):
    b = p.read_bytes(); parts = b.split(b'\n', 3)
    w, h = map(int, parts[1].split()); px = parts[3][:w*h*3]
    cols = len({px[i:i+3] for i in range(0, len(px), 3)})
    print(f"  {p.name:14} {w}x{h:<5} colours={cols:<6} {len(b)} bytes")
PY
echo
echo "=== serial tail ==="
[ -s "$OUT/serial.log" ] && tail -c 700 "$OUT/serial.log" || echo "(empty)"
