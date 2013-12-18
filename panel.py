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
from gi.repository import Wnck, Clutter, Gdk
import arrow # For time mangling.

import config # My config file handler.
from clock import ClockApplet

from math import floor

#from window_list import *
from workspace_indicator import Pager
from wmanagement import *

# Smooth scroll threshold which will be considered a workspace-changing scroll.
#SMOOTH_THRESHOLD = 0.8

def mk_colour(hex):
    stat, col = Clutter.Color.from_string(hex)

    if stat:
        return col
    else:
        raise Exception("Couldn't create a Clutter.Color from " + str(hex))

if __name__ == "__main__":
    Clutter.init(sys.argv)
    Gdk.init(sys.argv)

    # Load the screen.
    screen = Wnck.Screen.get_default()
    screen.force_update()

    def exit_cb(*args):
        global screen # Capture scope.
        screen = None
        
        Wnck.shutdown()
        Clutter.main_quit()

    stage = Clutter.Stage.get_default()
    stage.connect("destroy", exit_cb)
    stage.set_size(1366, 16)
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
    ws_list = get_used_workspaces()
        
#    screen.connect("window-opened", w_opened)
#    screen.connect("window-closed", w_closed)
                   
    pager = Pager(ws_list)
    box.add_actor(pager)

    # Bind window management events.
    screen.connect("active-workspace-changed",
                   lambda *args: pager.update(get_used_workspaces()))
    
    stage.show()
    Clutter.main()
