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
from math import floor
from pprint import pprint

# This has to come before the Clutter/Gtk/Wnck imports.
from gi.repository import GtkClutter
GtkClutter.init(sys.argv)

from gi.repository import Wnck, Clutter, Gtk, Gdk

# We need this to get the X11 ID for our panel window.
from gi.repository import GdkX11

# For time mangling.
import arrow

from WmInteraction import window_manager_menu, set_xprop_struts

from Pager import Pager
from PagerModel import *
from Taskbar import Taskbar

from Clock import ClockApplet
from Battery import BatteryApplet

class Panel(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, Gtk.WindowType.TOPLEVEL)
        self.connect("destroy", self.exit)

        # Load the screen.
        self.screen = Wnck.Screen.get_default()
        self.screen.force_update() # So our initial display is accurate.

        self.size = self.screen.get_width(), 16
        
        # Gtk hints and settings.
        self.set_size_request(*self.size)
        self.move(0, 0)
        self.set_title("cult panel")
        self.stick()

        # Also hides decoration and pager/tasklist.
        self.set_type_hint(Gdk.WindowTypeHint.DOCK)

        # Include the Clutter stage.
        self.embed = GtkClutter.Embed.new()
        self.add(self.embed)

        self.stage = self.embed.get_stage()
        self.stage.set_color(Clutter.Color.new(48, 48, 48, 255))

        # Layout and container bits.
        hlayout = Clutter.BinLayout.new(Clutter.BinAlignment.CENTER,
                                        Clutter.BinAlignment.CENTER)
        box = Clutter.Box.new(hlayout)
        box.set_size(*self.get_size_request())
        self.stage.add_actor(box)

        # Child widgets.
        self.widgets = {
            "clock": None,
            "battery": None,
            }
        
        # The taskbar.
        self.taskbar = Taskbar(self.screen, self.size[1])
        hlayout.add(self.taskbar,
                    Clutter.BinAlignment.START,
                    Clutter.BinAlignment.CENTER)

        # Applet box.
        applet_lo = Clutter.BoxLayout.new()
        applet_lo.set_spacing(8)
        self.widget_box = Clutter.Box.new(applet_lo)
        hlayout.add(self.widget_box,
                    Clutter.BinAlignment.END,
                    Clutter.BinAlignment.CENTER)

        ## Now, the various widgets.
        # Battery indicator.
        self.widgets["battery"] = \
          BatteryApplet(colour = Clutter.Color.new(255, 255, 255, 255))
        self.widget_box.add_actor(self.widgets["battery"])

        # The clock.
        self.widgets["clock"] = ClockApplet("HH:mm - DD.MM.YY",
                                            colour = Clutter.Color.new(255, 255,
                                                                       255, 255))
        self.widget_box.add_actor(self.widgets["clock"])

        # And the pager.
        self.pager = Pager(self.screen, height = self.size[1])
        hlayout.add(self.pager,
                    Clutter.BinAlignment.CENTER,
                    Clutter.BinAlignment.CENTER)

        # Bind workspace switching and assorted events.
        # At the moment, we only know how to open Fluxbox's menu.
        if self.screen.get_window_manager_name() == "Fluxbox":
            self.stage.connect("button-press-event", self.open_window_menu)

        # We can however change workspaces on anything that Wnck supports.
        self.SECS_PER_SCROLL = 0.35
        self.last_scroll = 0
        self.stage.connect("scroll-event", self.scroll_workspace)
            
        swipe = Clutter.SwipeAction.new()
        swipe.connect("swept", self.swipe_workspace)
        self.stage.add_action_with_name("SwipeWorkspace", swipe)
        
    def run(self):
        # Run the program.
        self.show_all()

        # Now that the window is realised, we need to set the strut request.
        xid = self.get_property("window").get_xid()
        set_xprop_struts(xid, 0, 0, self.get_size()[1], 0)

        Gtk.main()

    def exit(self, *args):
        # I don't know if this is actually necessary...
        self.screen = None
        
        Wnck.shutdown()
        Gtk.main_quit()

    def open_window_menu(self, actor, event):
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
                window_manager_menu()
            
    def scroll_workspace(self, actor, event, reverse = False):
        """ Change workspace by scrolling. """
        if event.type == Clutter.EventType.SCROLL:
            now = event.time

            if event.direction == Clutter.ScrollDirection.UP:
                if now - self.last_scroll > self.SECS_PER_SCROLL * 1000:
                    self.last_scroll = now
                    switch_workspace("next" if not reverse else "prev")

            elif event.direction == Clutter.ScrollDirection.DOWN:
                if now - self.last_scroll > self.SECS_PER_SCROLL * 1000:
                    self.last_scroll = now
                    switch_workspace("prev" if not reverse else "next")

    def swipe_workspace(self, action, actor, direction):
        if direction == Clutter.SwipeDirection.LEFT:
            switch_workspace("prev")
        elif direction == Clutter.SwipeDirection.RIGHT:
            switch_workspace("next")
