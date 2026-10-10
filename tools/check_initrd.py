#!/usr/bin/env python3
"""List a cpio initramfs without relying on lsinitramfs.

The shipped initrd is an uncompressed SVR4 cpio archive, which lsinitramfs
reported as 0 entries — a false negative that almost led me to conclude the
Plymouth theme was missing. This parses the archive directly.
"""
import pathlib
import sys


def cpio_names(path):
    """List every member across ALL concatenated cpio archives in the file.

    A Debian initramfs may be several archives back to back. An earlier version
    of this function stopped at the first TRAILER!!!, which would have missed
    everything in later archives - exactly the kind of false negative that
    already fooled me once with lsinitramfs.
    """
    d = pathlib.Path(path).read_bytes()
    names = []
    i = 0
    archives = 0
    while i + 110 <= len(d):
        if d[i:i + 6] not in (b"070701", b"070702"):
            nxt = d.find(b"070701", i)
            if nxt == -1:
                break
            i = nxt
            continue
        f = [int(d[i + 6 + 8 * k:i + 6 + 8 * (k + 1)], 16) for k in range(13)]
        namesize, filesize = f[11], f[6]
        if namesize == 0 or namesize > 4096:
            nxt = d.find(b"070701", i + 6)
            if nxt == -1:
                break
            i = nxt
            continue
        name = d[i + 110:i + 110 + namesize - 1].decode("utf-8", "replace")
        names.append(name)
        i += 110 + namesize
        i += (-i) % 4
        i += filesize
        i += (-i) % 4
        if name == "TRAILER!!!":
            archives += 1
            # skip to the next archive rather than stopping
            while i % 4:
                i += 1
            nxt = d.find(b"070701", i)
            if nxt == -1:
                break
            i = nxt
    return names, archives


def report(label, path):
    f = pathlib.Path(path)
    if not f.exists():
        print("%s: MISSING" % label)
        return
    n, archives = cpio_names(path)
    ply = [x for x in n if "plymouth" in x.lower()]
    themes = sorted({x.split("plymouth/themes/")[1].split("/")[0]
                     for x in n if "plymouth/themes/" in x})
    print("%s" % label)
    print("   size            : %d MB" % (f.stat().st_size // 1048576))
    print("   cpio archives   : %d" % archives)
    print("   entries         : %d" % len(n))
    print("   plymouth entries: %d" % len(ply))
    print("   themes present  : %s" % (themes if themes else "(none)"))
    print("   has plymouthd   : %s" % any(x.endswith("sbin/plymouthd") for x in n))
    print("   has splash      : %s" % any("plymouth" in x and "splash" in x for x in n))
    print("")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            report(pathlib.Path(arg).name, arg)
    else:
        base = "/root/himal"
        report("binary/live  (what ships in the ISO)",
               base + "/binary/live/initrd.img-6.12.111+deb13-arm64")
        report("chroot/boot  (the chroot's own copy)",
               base + "/chroot/boot/initrd.img-6.12.111+deb13-arm64")
