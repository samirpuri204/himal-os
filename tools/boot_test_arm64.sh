#!/bin/sh
# Boot the Himal OS arm64 ISO headlessly under QEMU with real UEFI firmware,
# capturing the guest framebuffer as evidence.
#
# This is the test ReactOS never passed: an arm64 guest booting on an arm64 Mac.
set -u

QEMU=/opt/homebrew/bin/qemu-system-aarch64
ISO=/Users/samir/Downloads/himal-os-debian/dist/Himal-OS-13-arm64-xfce.iso
FW=/opt/homebrew/share/qemu/edk2-aarch64-code.fd
OUT=/Users/samir/Downloads/himal-os-debian/boottest
SOCK=$OUT/monitor.sock
FIFO=$OUT/cmd.fifo

mkdir -p "$OUT"
rm -f "$SOCK" "$FIFO" "$OUT"/*.ppm "$OUT"/serial.log "$OUT"/qemu.stdout "$OUT"/monitor.out

[ -x "$QEMU" ] || { echo "ERROR: $QEMU missing"; exit 1; }
[ -f "$ISO" ]  || { echo "ERROR: ISO missing"; exit 1; }
[ -f "$FW" ]   || { echo "ERROR: UEFI firmware missing"; exit 1; }

echo "ISO  : $ISO"
echo "size : $(stat -f%z "$ISO") bytes"
echo "UEFI : $FW"
echo "accel: trying hvf (Apple Hypervisor), falling back to tcg"

start_qemu() { # start_qemu <accel-flags...>
    "$QEMU" -M virt -m 2048 -smp 2 "$@" \
        -bios "$FW" \
        -device virtio-gpu-pci \
        -display none \
        -cdrom "$ISO" \
        -monitor unix:"$SOCK",server,nowait \
        -serial "file:$OUT/serial.log" \
        -no-reboot \
        >>"$OUT/qemu.stdout" 2>&1 &
    QPID=$!
}

start_qemu -accel hvf -cpu host
sleep 6
if ! kill -0 "$QPID" 2>/dev/null || [ ! -S "$SOCK" ]; then
    echo "  hvf unavailable, retrying with tcg (slower)"
    kill "$QPID" 2>/dev/null; wait "$QPID" 2>/dev/null
    rm -f "$SOCK"
    start_qemu -accel tcg -cpu max
    sleep 6
fi

for _ in $(seq 1 40); do [ -S "$SOCK" ] && break; sleep 0.5; done
if [ ! -S "$SOCK" ]; then echo "ERROR: monitor socket never appeared"; cat "$OUT/qemu.stdout"; exit 1; fi

mkfifo "$FIFO"
nc -U "$SOCK" <"$FIFO" >"$OUT/monitor.out" 2>&1 &
NCPID=$!
exec 3>"$FIFO"
mon() { printf '%s\n' "$1" >&3; }

echo
echo "--- capturing frames ---"
cum=0
for d in 15 15 20 30 40 60; do
    sleep "$d"; cum=$((cum + d))
    if ! kill -0 "$QPID" 2>/dev/null; then echo "  guest exited before t=${cum}s"; break; fi
    mon "screendump $OUT/f_${cum}.ppm"
    echo "  t=${cum}s captured"
done

echo "quit" >&3 2>/dev/null
exec 3>&- 2>/dev/null
sleep 1
kill "$NCPID" 2>/dev/null

echo
echo "=== frames (hash + size) ==="
for f in "$OUT"/*.ppm; do
    [ -f "$f" ] || continue
    printf "  %-26s %10s bytes  %s\n" "$(basename "$f")" "$(stat -f%z "$f")" "$(shasum -a 256 "$f" | cut -c1-16)"
done

echo
echo "=== distinct screens ==="
shasum -a 256 "$OUT"/*.ppm 2>/dev/null | awk '{print substr($1,1,16)}' | sort -u | wc -l

echo
echo "=== serial log ==="
if [ -s "$OUT/serial.log" ]; then head -c 2000 "$OUT/serial.log"; else echo "(empty)"; fi
echo
echo "=== qemu stdout/stderr ==="
head -c 1500 "$OUT/qemu.stdout"
