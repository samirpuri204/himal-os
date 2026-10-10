# Using Himal OS

Everything below runs from a terminal as the `himal` user. Most of it is also in
the application menu under **System**.

---

## The `himal` command

One command covers the whole system.

```bash
himal                       # branded system information
himal features              # what makes this system different
himal about                 # About window
himal credit                # who built it

himal control-center        # quick settings
himal studio                # themes, wallpapers, icons, layouts
himal dashboard             # CPU, memory, disk, network, updates
himal security              # firewall, updates, ports, hardening
himal recovery              # snapshots and guided repair
himal performance           # Eco / Balanced / Performance
himal apphub                # APT, Flatpak and AppImage
himal launcher              # application search and power controls
himal calendar              # the date, in Nepali as well as English

himal layout mac            # macOS-style: top bar, floating dock
himal layout windows        # Windows-style: bottom taskbar, Start menu
himal wallpaper dusk        # change wallpaper live
himal accent light          # light/dark appearance
himal update                # update the system
```

---

## Desktop layouts

Two layouts ship in one image. Neither needs a reinstall or a logout.

**macOS style** (default) — a top bar with the Himal menu on the left and a
centred clock, a floating translucent dock along the bottom, and window controls
on the **left**.

**Windows style** — a single bottom taskbar with a Start-style menu, labelled
window buttons, and window controls on the **right**.

```bash
himal layout mac
himal layout windows
```

Under the hood these set Xfce panel and `xfwm4` properties through
`xfconf-query`, so they apply immediately.

---

## Appearance

The **Personalization Studio** (`himal studio`) covers theme, icon pack, accent
colour, wallpaper and layout. It also has a *Use Nepali Fonts* toggle.

Wallpapers ship in four variants — `abyss`, `dusk`, `ice` (light) and `ember`:

```bash
himal wallpaper          # list them
himal wallpaper ember    # apply one
```

The desktop compositor provides rounded window corners, shadows, blur and smooth
window fading. Its configuration is at `/etc/xdg/picom/picom.conf`; disable it by
removing `/etc/xdg/autostart/himal-compositor.desktop` if you prefer the
uncomposited fallback.

---

## Security

```bash
sudo ufw status                  # firewall state
himal security                   # full dashboard with a scan
```

Defaults on a fresh install: automatic security updates enabled, firewall on with
`deny incoming`, AppArmor active, and fail2ban installed. Risky actions in the
Himal tools ask for confirmation before making changes.

---

## Snapshots and recovery

```bash
himal recovery                   # guided repair and snapshot management
```

If a system update leaves things broken, the **Repair** tab walks through safe,
reversible fixes for broken updates, package errors, networking, display
configuration and panels.

---

## Installing software

The **Universal App Hub** (`himal apphub`) searches APT packages and Flatpak apps
in one place, and shows the **source** of every result before you install it.

```bash
flatpak remote-add --if-not-exists flathub \
  https://flathub.org/repo/flathub.flatpakrepo
```

---

## Nepal-first defaults

- Timezone: **Asia/Kathmandu**
- Keyboard: **`us,np`** — switch between them with **Super+Space**
- Fonts: Noto and Lohit Devanagari
- Locales: `en_US.UTF-8` and `ne_NP`

```bash
himal calendar
```

prints the date in English and Nepali, with the weekday and month names in
Devanagari.

> Full Bikram Sambat conversion needs an authoritative month-length table, so it
> is deliberately not faked here — only the names are localised, which is always
> correct.

---

## The developer credit

The credit **"Build by Samir Puri"** is part of the system by design:

- baked into the desktop wallpaper
- shown on the boot splash
- on the login banner (`/etc/issue`)
- in the About window
- in `~/HIMAL-OS-CREDIT.txt` and `~/HIMAL-OS-CREDIT.md`

The home-directory copies are root-owned, mode 444, with the immutable attribute
set, and a systemd timer restores them if they are removed or edited.

To be straight about the limits: this makes the credit very hard to remove in
normal use, but on a Linux system with root access nothing is truly permanent —
`chattr -i` and a delete will still work. It is a strong deterrent, not an
absolute guarantee.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| No boot splash | Known issue — see the status table in the README |
| Black screen after boot | Ensure the hypervisor uses UEFI, and that you are running arm64 natively (`Virtualize` in UTM, not `Emulate`) |
| Window buttons on the wrong side | `himal layout mac` (or `windows`) |
| Wallpaper reverts | `himal wallpaper abyss` — session defaults reapply at login |
| Slow performance | `himal performance` and choose **Performance** |
| Broken packages | `himal recovery` → Repair tab |
