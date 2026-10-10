#!/bin/sh
# Build Himal OS inside the native arm64 himal-deb container.
#
# Config lives on the host (editable, persistent) and is copied into the
# container so the actual build runs on the container's own filesystem rather
# than over the virtiofs mount, which is much faster for debootstrap.
#
# Usage:
#   sh build.sh config   # only re-run lb config (fast, validates the config)
#   sh build.sh build    # full build -> /build/dist/
set -eu

DOCKER_HOST=unix:///Users/samir/.colima/default/docker.sock
export DOCKER_HOST
DOCKER_CONFIG=/Users/samir/Downloads/himal-os/build/dockercfg
export DOCKER_CONFIG
PROJ=/Users/samir/Downloads/himal-os-debian
STAGE="${1:-build}"

echo "=== staging config into container ==="
docker exec himal-deb bash -lc 'rm -rf /root/himal && mkdir -p /root/himal'
docker cp "$PROJ/auto"   himal-deb:/root/himal/auto
docker cp "$PROJ/config" himal-deb:/root/himal/config
docker exec himal-deb bash -lc 'chmod +x /root/himal/auto/config && ls /root/himal/config'

if [ "$STAGE" = "config" ]; then
    echo "=== running lb config ==="
    docker exec himal-deb bash -lc 'cd /root/himal && lb config 2>&1 | tail -20; echo "EXIT=${PIPESTATUS[0]}"; echo; echo "--- generated config dir ---"; ls -a config | head -30'
    exit 0
fi

echo "=== full build ==="
docker exec himal-deb bash -lc '
set -e
cd /root/himal
lb build 2>&1 | tee /root/build.log | tail -40
echo "EXIT=${PIPESTATUS[0]}"
'
echo "=== collect artefacts ==="
mkdir -p "$PROJ/dist"
docker exec himal-deb bash -lc 'ls -la /root/himal/*.iso /root/himal/*.hybrid.iso 2>/dev/null' || true
for iso in $(docker exec himal-deb bash -lc 'ls /root/himal/*.iso /root/himal/*.hybrid.iso 2>/dev/null'); do
    docker cp "himal-deb:$iso" "$PROJ/dist/$(basename "$iso")" && echo "copied $(basename "$iso")"
done
ls -la "$PROJ/dist" 2>/dev/null || echo "(no ISO produced)"
