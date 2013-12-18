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
from gi.repository import GtkClutter
GtkClutter.init(sys.argv)

from gi.repository import Wnck, Clutter, Gtk, Gdk
import arrow # For time mangling.

import config # My config file handler.
from clock import ClockApplet

from math import floor
from pprint import pprint

#from window_list import *
from Pager import Pager
from PagerModel import *

# Smooth scroll threshold which will be considered a workspace-changing scroll.
#SMOOTH_THRESHOLD = 0.8

def mk_colour(hex):
    stat, col = Clutter.Color.from_string(hex)

    if stat:
        return col
    else:
        raise Exception("Couldn't create a Clutter.Color from " + str(hex))

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
    win.set_decorated(False)
    win.set_skip_pager_hint(True)
    win.set_skip_taskbar_hint(True)
    win.set_type_hint(Gdk.WindowTypeHint.DOCK)
    
    # Load the screen.
    screen = Wnck.Screen.get_default()
    screen.force_update()

    def exit_cb(*args):
        global screen # Capture the right scope.
        screen = None
        
        Wnck.shutdown()
        Gtk.main_quit()

    win.connect("destroy", exit_cb)

    stage = embed.get_stage()
    stage.set_color(Clutter.Color.new(48, 48, 48, 255))

    # Layout.
    hlayout = Clutter.BoxLayout.new()
    hlayout.set_vertical(False)
    hlayout.set_spacing(4)
    box = Clutter.Box.new(hlayout)
    stage.add_actor(box)

    # This seems to be necessary so that the text aligns properly.
    qq = Clutter.Rectangle.new()
    qq.set_size(0, 18)
    qq.set_color(Clutter.Color.new(0, 0, 0, 255))
    box.add_actor(qq)

    # The clock.
    rr = ClockApplet("hh:mm:ss",
                     colour = Clutter.Color.new(0, 0, 0, 255))
    box.add_actor(rr)

    # And the pager.                   
    pager = Pager()
    box.add_actor(pager)

    # Bind window management events.
    screen.connect("active-workspace-changed", pager.update)
    screen.connect("window-opened", pager.update)
    screen.connect("window-closed", pager.update)
    
#    stage.show()
#    Clutter.main()
    win.show_all()
    Gtk.main()
