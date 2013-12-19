#!/usr/bin/env python3

__docstring__ = """
                cultpanel - Crappy Useless LiTtle Panel
  Aims:
    We need a clock, a battery indicator, a date indicator.
    A workspace indicator with dots like iOS is also desirable.
    Window list would be nice but non-essential.

  What this isn't (yet):
    Systray. Unfortunately, that looks reeeallly difficult/awful to make.
    Extensible. I can't be bothered.
    For general consumption. Code is "for my eyes only" so things might not be well designed or reusable. It should be fairly small/nifty though.

    by Ryan Gray, 2013
"""

import sys
from subprocess import call as call_process
from gi.repository import GtkClutter
GtkClutter.init(sys.argv)

from gi.repository import Wnck, Clutter, Gtk, Gdk
import arrow # For time mangling.

import config # My config file handler.

from math import floor
from pprint import pprint

from Pager import Pager
from PagerModel import *
from Taskbar import Taskbar

from Clock import ClockApplet
from Battery import BatteryApplet

def window_menu(actor, event):
    """ Open the host WM's desktop menu.

    In Fluxbox, this is bound to right-click, so we'll do the same.
    """
    if event.button == 3:
        # The actor parameter is always the stage.
        # We need to make sure not to get confused with the taskbar.
        target = actor.get_actor_at_pos(Clutter.PickMode.REACTIVE,
                                        event.x, event.y)
        if target is actor:
            # We've clicked the stage. We can open the menu.
            call_process(["fluxbox-remote", "RootMenu"])

SECS_PER_SCROLL = 0.35
_last_scroll = 0
def scroll_workspace(actor, event, reverse = False):
    """ Change workspace by scrolling. """
    if event.type == Clutter.EventType.SCROLL:
        global _last_scroll
        now = event.time

        if event.direction == Clutter.ScrollDirection.UP:
            if now - _last_scroll > SECS_PER_SCROLL * 1000:
                _last_scroll = now
                switch_workspace("next" if not reverse else "prev")

        elif event.direction == Clutter.ScrollDirection.DOWN:
            if now - _last_scroll > SECS_PER_SCROLL * 1000:
                _last_scroll = now
                switch_workspace("prev" if not reverse else "next")

def swipe_workspace(action, actor, direction):
    if direction == Clutter.SwipeDirection.LEFT:
        switch_workspace("prev")
    elif direction == Clutter.SwipeDirection.RIGHT:
        switch_workspace("next")
        
if __name__ == "__main__":
    # Gtk application window.
    win = Gtk.Window.new(Gtk.WindowType.TOPLEVEL)
    embed = GtkClutter.Embed.new()
    win.add(embed)

    # Gtk hints and settings.
    win.set_size_request(1366, 16)
    win.move(0, 0)
    win.set_title("cult panel")
    win.stick()
    win.set_type_hint(Gdk.WindowTypeHint.DOCK) # Also hides decoration and pager/tasklist.
    
    # Load the screen.
    screen = Wnck.Screen.get_default()
    screen.force_update() # So our initial display is accurate.

    def exit_cb(*args):
        # I don't know if this is actually necessary...
        global screen # Capture the right scope.
        screen = None
        
        Wnck.shutdown()
        Gtk.main_quit()

    win.connect("destroy", exit_cb)

    stage = embed.get_stage()
    stage.set_color(Clutter.Color.new(48, 48, 48, 255))

    # Layout and container bits.
    hlayout = Clutter.BinLayout.new(Clutter.BinAlignment.CENTER,
                                    Clutter.BinAlignment.CENTER)
    box = Clutter.Box.new(hlayout)
    box.set_size(*win.get_size_request())
    stage.add_actor(box)

    # The taskbar.
    taskbar = Taskbar()
    hlayout.add(taskbar, Clutter.BinAlignment.START, Clutter.BinAlignment.CENTER)

    # Applet box.
    applet_lo = Clutter.BoxLayout.new()
    applet_lo.set_spacing(8)
    applet_box = Clutter.Box.new(applet_lo)
    hlayout.add(applet_box,
                Clutter.BinAlignment.END,
                Clutter.BinAlignment.CENTER)
    
    # Battery indicator.
    batt = BatteryApplet(colour = Clutter.Color.new(255, 255, 255, 255))
    applet_box.add_actor(batt)

    # The clock.
    clock = ClockApplet("HH:mm - DD.MM.YY",
                        colour = Clutter.Color.new(255, 255, 255, 255))
    applet_box.add_actor(clock)

    # And the pager.
    pager = Pager(screen)
    hlayout.add(pager, Clutter.BinAlignment.CENTER, Clutter.BinAlignment.CENTER)

    # Bind workspace switching and assorted events.
    # At the moment, we only know how to open Fluxbox's menu.
    if screen.get_window_manager_name() == "Fluxbox":
        stage.connect("button-press-event", window_menu)
    stage.connect("scroll-event", scroll_workspace)

    swipe = Clutter.SwipeAction.new()
    swipe.connect("swept", swipe_workspace)
    stage.add_action_with_name("SwipeWorkspace", swipe)
        
    # Run the program.
    win.show_all()
    Gtk.main()
