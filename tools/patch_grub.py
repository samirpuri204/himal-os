#!/usr/bin/env python3
"""Brand the shipped grub.cfg and give it a boot timeout.

Two real defects in the built ISO:

  1. The generated grub.cfg has no 'set timeout=' and no 'set default=', so GRUB
     waits for a keypress forever. Nobody can boot it unattended.
  2. The menu entries read "Live system (arm64)" rather than naming Himal OS.

This takes the grub.cfg that live-build actually produced (extracted from the
built ISO, so the structure is exactly what works) and applies only those two
changes, then writes it to config/bootloaders/grub-pc/grub.cfg so live-build
uses ours instead of its default.

Credit: Build by Samir Puri
"""
import pathlib
import re
import subprocess
import sys

ISO = "dist/Himal-OS-13-arm64-xfce.iso"
DEST = pathlib.Path("config/bootloaders/grub-pc/grub.cfg")

# menu entry label -> branded label
RENAMES = [
    ("Live system (arm64 fail-safe mode)", "Himal OS Live (fail-safe mode)"),
    ("Live system (arm64)", "Himal OS Live (arm64)"),
]


def extract_shipped_cfg(tmp=".grub_extract"):
    p = pathlib.Path(tmp)
    p.mkdir(exist_ok=True)
    subprocess.run(["tar", "-xf", ISO, "-C", tmp, "boot/grub/grub.cfg"], check=True)
    return (p / "boot/grub/grub.cfg").read_text(encoding="utf-8", errors="surrogateescape")


def main():
    cfg = extract_shipped_cfg()

    if "set timeout" in cfg:
        print("  NOTE: shipped cfg already has a timeout; leaving as-is")

    # 1. insert the timeout right after the config.cfg source line
    anchor = "source /boot/grub/config.cfg"
    if anchor not in cfg:
        print("ERROR: anchor line not found; aborting", file=sys.stderr)
        return 1
    insert = ("source /boot/grub/config.cfg\n"
              "\n"
              "# Himal OS: boot the default entry automatically after 10 seconds.\n"
              "set timeout=10\n"
              "set default=0\n")
    cfg = cfg.replace(anchor + "\n", insert, 1)

    # 2. brand the menu entry labels (plain substring replace, order matters:
    #    the longer label contains the shorter one)
    for old, new in RENAMES:
        before = cfg
        cfg = cfg.replace(f'"{old}"', f'"{new}"')
        cfg = cfg.replace(old, new)
        print(f"  renamed: {old!r} -> {new!r} ({'ok' if cfg != before else 'NOT FOUND'})")

    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(cfg, encoding="utf-8", errors="surrogateescape")
    print(f"\n  wrote {DEST} ({len(cfg)} bytes)")
    print(f"  timeout present: {'set timeout=' in cfg}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
