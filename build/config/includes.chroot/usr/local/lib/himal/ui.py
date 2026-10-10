#!/usr/bin/env python3
"""Shared UI helpers for Himal OS applications. Build by Samir Puri."""
import subprocess

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk  # noqa: E402

ACCENT = "#1698D2"

_CSS = """/* Himal OS application styling. Build by Samir Puri */
@define-color himal_accent #1698D2;
@define-color himal_accent_dim #1268A8;
@define-color himal_navy #070E2A;
@define-color himal_card #0d1830;

window, .background { background-color: @himal_navy; }

headerbar {
    background-image: none;
    background-color: #0a1430;
    border-bottom: 1px solid alpha(@himal_accent, 0.25);
    min-height: 44px;
    box-shadow: none;
}
headerbar .title { font-weight: 600; letter-spacing: 0.3px; }

.himal-brand {
    color: @himal_accent;
    font-weight: 700;
    letter-spacing: 1.6px;
    font-size: 92%;
}

.card {
    background-color: @himal_card;
    border: 1px solid alpha(@himal_accent, 0.22);
    border-radius: 14px;
    padding: 14px;
}

.card-title { font-weight: 600; font-size: 105%; }
.card-sub   { color: #8ea3bb; font-size: 88%; }
.big-value  { font-size: 190%; font-weight: 700; color: #eaf2fb; }
.dim        { color: #8ea3bb; font-size: 90%; }
.section    { color: @himal_accent; font-weight: 700; font-size: 85%; letter-spacing: 1px; }
.credit     { color: #7d93ab; font-size: 85%; }

button.suggested-action {
    background-image: none;
    background-color: @himal_accent;
    color: #ffffff;
    border: none;
}
button.suggested-action:hover { background-color: #1aa9e8; }

button.flat:hover { background-color: alpha(@himal_accent, 0.18); }

switch:checked { background-color: @himal_accent; }

levelbar block.filled { background-color: @himal_accent; }
levelbar block.high   { background-color: #e0a24a; }
levelbar block.full   { background-color: #e05a6a; }

progressbar progress { background-color: @himal_accent; }

list { background-color: transparent; }
row { padding: 6px 2px; }

.sidebar { background-color: #091026; }
"""


def apply_theme():
    """Install the Himal stylesheet for this process."""
    screen = Gdk.Screen.get_default()
    if screen is None:
        return
    provider = Gtk.CssProvider()
    provider.load_from_data(_CSS.encode("utf-8"))
    Gtk.StyleContext.add_provider_for_screen(
        screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )


def sh(cmd, timeout=12):
    """Run a shell command, return stripped stdout (never raises)."""
    try:
        out = subprocess.run(cmd, shell=True, capture_output=True,
                             text=True, timeout=timeout)
        return (out.stdout or "").strip()
    except Exception:
        return ""


def sh_ok(cmd, timeout=12):
    """Run a command, return True on exit status 0."""
    try:
        return subprocess.run(cmd, shell=True, capture_output=True,
                              timeout=timeout).returncode == 0
    except Exception:
        return False


def win(title, subtitle=None, width=460, height=560):
    """A Himal window: header bar with the brand on the left, app title beside it."""
    w = Gtk.Window()
    w.set_title(title)
    w.set_default_size(width, height)
    w.set_border_width(0)

    hb = Gtk.HeaderBar()
    hb.set_show_close_button(True)
    brand = Gtk.Label(label="Himal OS")
    brand.get_style_context().add_class("himal-brand")
    hb.pack_start(brand)

    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
    hb.set_custom_title(None)
    hb.props.title = title
    w.set_titlebar(hb)

    outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    outer.set_border_width(14)
    box.pack_start(outer, True, True, 0)

    if subtitle:
        sub = Gtk.Label(label=subtitle, xalign=0)
        sub.get_style_context().add_class("dim")
        outer.pack_start(sub, False, False, 0)

    return w, outer


def card(title=None, subtitle=None):
    """A rounded card container, optionally titled. Returns (box, content)."""
    frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    frame.get_style_context().add_class("card")
    if title:
        t = Gtk.Label(label=title, xalign=0)
        t.get_style_context().add_class("card-title")
        frame.pack_start(t, False, False, 0)
    if subtitle:
        s = Gtk.Label(label=subtitle, xalign=0)
        s.get_style_context().add_class("card-sub")
        frame.pack_start(s, False, False, 0)
    content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    frame.pack_start(content, False, False, 0)
    return frame, content


def row(label, control, sub=None):
    """A settings row: label (+ optional dim subtitle) on the left, control right."""
    b = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
    lab = Gtk.Label(label=label, xalign=0)
    left.pack_start(lab, False, False, 0)
    if sub:
        s = Gtk.Label(label=sub, xalign=0)
        s.get_style_context().add_class("card-sub")
        left.pack_start(s, False, False, 0)
    b.pack_start(left, True, True, 0)
    b.pack_end(control, False, False, 0)
    return b


def switch(active, on_change):
    sw = Gtk.Switch()
    sw.set_active(bool(active))
    sw.connect("state-set", lambda _w, state: (on_change(state), False)[1])
    return sw


def button(label, on_click, suggested=False):
    b = Gtk.Button(label=label)
    if suggested:
        b.get_style_context().add_class("suggested-action")
    b.connect("clicked", lambda _w: on_click())
    return b


def slider(value, lo, hi, on_change):
    s = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, lo, hi, 1)
    s.set_value(value)
    s.set_size_request(180, -1)
    s.connect("value-changed", lambda w: on_change(w.get_value()))
    return s


def dropdown(options, active_index, on_change):
    c = Gtk.ComboBoxText()
    for o in options:
        c.append_text(o)
    c.set_active(max(0, min(active_index, len(options) - 1)))
    c.connect("changed", lambda w: on_change(w.get_active()))
    return c


def scroller(child):
    sc = Gtk.ScrolledWindow()
    sc.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    sc.add(child)
    return sc


def stack(sections):
    """sections: list of (name, widget). Returns (container, stack) with a switcher."""
    st = Gtk.Stack()
    st.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
    for name, widget in sections:
        st.add_titled(widget, name.lower().replace(" ", "-"), name)
    sw = Gtk.StackSwitcher()
    sw.set_stack(st)
    sw.set_halign(Gtk.Align.CENTER)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    box.pack_start(sw, False, False, 0)
    box.pack_start(st, True, True, 0)
    return box, st


def credit_line():
    l = Gtk.Label(label="Build by Samir Puri", xalign=0)
    l.get_style_context().add_class("credit")
    return l


def run_app(build):
    """Standard entry point: apply theme, build, show, run."""
    apply_theme()
    w = build()
    w.connect("destroy", Gtk.main_quit)
    w.show_all()
    Gtk.main()
