# Building Himal OS

Everything here was learned by actually running the build, including the parts
that went wrong. The notes at the end are the ones that cost the most time.

---

## Requirements

- A machine that can run **arm64** containers (an Apple Silicon Mac, or an arm64
  Linux box). Building on x86 with emulation works but is far slower.
- Docker or a compatible container runtime
- ~25 GB free disk
- Network access to the Debian archive

No ReactOS Build Environment, no cross toolchain, no custom GCC. Debian's own
`live-build` does all of it.

---

## 1. Create the build container

```bash
docker run -d --privileged --platform linux/arm64 \
  --name himal-deb \
  -v "$PWD/build:/build" \
  debian:trixie sleep infinity
```

**`--privileged` is not optional.** `live-build` mounts `/proc`, `/sys` and
`/dev/pts` inside its chroot, and Docker drops `CAP_SYS_ADMIN` by default. Without
it the build dies with:

```
mount: /build/chroot/dev/pts: permission denied.
E: An unexpected failure occurred, exiting...
```

## 2. Install the toolchain

```bash
docker exec himal-deb bash -lc '
  apt-get update
  apt-get install -y --no-install-recommends \
    live-build debootstrap squashfs-tools xorriso \
    grub-efi-arm64-bin grub-common mtools dosfstools \
    git curl ca-certificates zstd xz-utils gpg file'
```

## 3. Generate the overlay

The files under `build/config/includes.chroot/` are **generated**, so they can be
reproduced rather than hand-maintained:

```bash
cd tools
for s in make_assets make_splash make_overlay make_grub_branding \
         make_himal_apps make_credit make_himal_desktop make_himal_ui \
         make_himal_apps1 make_himal_apps2 make_himal_system make_himal_session; do
  python3 "$s.py"
done
```

## 4. Build

```bash
docker exec himal-deb bash -lc 'cd /build && lb build'
```

Takes roughly **30–45 minutes**. The phases that dominate the time:

| Phase | Typical |
|---|---|
| Bootstrap (debootstrap) | ~3–6 min |
| Download + install pass | ~15–25 min |
| Live pass (package lists) | ~10–15 min |
| `mksquashfs` (`-comp xz`) | ~8 min |
| GRUB EFI + `xorriso` | ~2 min |

The output is `build/live-image-arm64.hybrid.iso`.

## 5. Verify

```bash
sh tools/verify_iso.sh
```

It reads everything back **out of the finished ISO** rather than trusting that it
was staged. That method caught three real bugs. It checks boot records, volume
branding, the GRUB menu and timeout, the EFI loader, every `himal-*` command, the
Plymouth theme, the credit system, Nepal-first defaults, and that no stray
directories exist at the image root.

## 6. Boot-test

```bash
sh tools/boot_capture_fine.sh
```

Boots the ISO under QEMU with real arm64 UEFI firmware and captures the guest
framebuffer every 2 seconds through the splash window, then coarsely to the
desktop.

---

## Problems that cost real time

### Release the chroot mounts before deleting the build tree

`live-build` leaves `/proc`, `/sys` and `/dev/pts` mounted inside the chroot. A
lazy unmount (`umount -l`) detaches them without freeing the directories, so
`rm -rf build/chroot` silently fails on those paths and the next `debootstrap`
runs into a corrupted tree:

```
I: Extracting util-linux...
E: An unexpected failure occurred, exiting...
```

Do it properly, and verify before deleting:

```bash
for m in $(grep -oE '/build/chroot[^ ]*' /proc/mounts | sort -ru); do
  umount -l "$m" 2>/dev/null || umount -f "$m" 2>/dev/null
done
grep /build/chroot /proc/mounts | wc -l    # must be 0
```

The same mistake also silently discards the ~2 GB package cache, which lives at
`chroot/var/cache/apt/archives`. Use `lb clean --binary` to keep the chroot.

### A relative overlay path silently does nothing

`config/includes.chroot/xdg/picom/picom.conf` installs to `/xdg/picom/picom.conf`,
not `/etc/xdg/...`. The file is "present" in the build and ignored by the system.
The same applies to `gtk-3.0/gtk.css` versus `etc/gtk-3.0/gtk.css`.

`verify_iso.sh` now fails loudly if a stray top-level directory appears at the
image root.

### `/etc/xdg` defaults lose to user configuration

Config placed in `/etc/xdg/xfce4/xfconf/xfce-perchannel-xml/` is a *default*. On
Debian the live user's own config and desktop-base's XDG profile take precedence,
so the wallpaper and window-button settings were silently overridden even though
the files were correct.

Apply appearance at session start with `xfconf-query`, which writes **user-level**
values that always win — see `himal-session-defaults`.

### `getty` eats backslashes in `/etc/issue`

`getty` interprets backslash escapes (`\n` = hostname, `\l` = tty), so a literal
backslash must be written doubled or ASCII art renders mangled.

### Trust `cpio`, not `lsinitramfs`

`lsinitramfs` reported **0 entries** for this initrd (an uncompressed SVR4 cpio),
which nearly led to the wrong conclusion about the boot splash. A Debian initramfs
may also be several cpio archives concatenated, so a parser that stops at the
first `TRAILER!!!` will miss everything after it.
