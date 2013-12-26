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

from gi.repository import GtkClutter, Wnck, Clutter, Gtk, Gdk

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
    def __init__(self, conf):
        Gtk.Window.__init__(self, Gtk.WindowType.TOPLEVEL)
        self.connect("destroy", self.exit)

        self.conf = conf
        
        # Load the screen.
        self.screen = conf.getscreen()
        self.screen.force_update() # So our initial display is accurate.

        # Set up the pager model.
        conf.getpagermodel()

        # Work out the orientation.
        self.orientation = conf.get("Panel", "orientation")
        if self.orientation in ["bottom", "top"]:
            self.size = self.screen.get_width(), conf.getint("Panel", "size")
        else:
            self.size = conf.getint("Panel", "size"), self.screen.get_height()

        # Gtk hints and settings.
        self.set_size_request(*self.size)
        self.set_title("cult panel")
        self.stick()

        # Also hides decoration and pager/tasklist.
        self.set_type_hint(Gdk.WindowTypeHint.DOCK)

        # Include the Clutter stage.
        self.embed = GtkClutter.Embed.new()
        self.add(self.embed)

        self.stage = self.embed.get_stage()
        self.stage.set_color(conf.getcolour("Panel", "background"))

        # Layout and container bits.
        hlayout = Clutter.BinLayout.new(Clutter.BinAlignment.CENTER,
                                        Clutter.BinAlignment.CENTER)
        box = Clutter.Box.new(hlayout)
        box.set_size(*self.size)
        self.stage.add_actor(box)

        # Child widgets.
        self.widgets = {
            "clock": None,
            "battery": None,
            }
        
        # The taskbar.
        self.taskbar = Taskbar(conf, self.size)
        hlayout.add(self.taskbar,
                    Clutter.BinAlignment.START,
                    Clutter.BinAlignment.CENTER)

        # Applet box.
        applet_lo = Clutter.BoxLayout.new()
        applet_lo.set_spacing(8)
        if conf.is_vertical(): applet_lo.set_vertical(True)
        
        self.widget_box = Clutter.Box.new(applet_lo)
        hlayout.add(self.widget_box,
                    Clutter.BinAlignment.END,
                    Clutter.BinAlignment.CENTER)

        ## Now, the various widgets.
        # Battery indicator.
        self.widgets["battery"] = BatteryApplet(conf)
        self.widget_box.add_actor(self.widgets["battery"])

        # The clock.
        self.widgets["clock"] = ClockApplet(conf)
        self.widget_box.add_actor(self.widgets["clock"])

        # And the pager.
        self.pager = Pager(conf)
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

    def setup_visuals(self):
        # Run the program.
        self.show_all()

        # Now that the window is realised, we will need to set the strut request.
        xid = self.get_property("window").get_xid()

        # Move ourselves to the right place, and set the right strut.
        if self.orientation == "top":
            self.move(0, 0)
            set_xprop_struts(xid, 0, 0, self.size[1], 0)
        elif self.orientation == "bottom":
            self.move(0, self.screen.get_height() - self.size[1])
            set_xprop_struts(xid, 0, 0, 0, self.size[1])
        elif self.orientation == "left":
            self.move(0, 0)
            set_xprop_struts(xid, self.size[0], 0, 0, 0)
        elif self.orientation == "right":
            self.move(self.screen.get_width() - self.size[0], 0)
            set_xprop_struts(xid, 0, self.size[0], 0, 0)

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
                    switch_workspace(self.conf,
                                     "next" if not reverse else "prev")

            elif event.direction == Clutter.ScrollDirection.DOWN:
                if now - self.last_scroll > self.SECS_PER_SCROLL * 1000:
                    self.last_scroll = now
                    switch_workspace(self.conf,
                                     "prev" if not reverse else "next")

    def swipe_workspace(self, action, actor, direction):
        if direction == Clutter.SwipeDirection.LEFT:
            switch_workspace(self.conf, "prev")
        elif direction == Clutter.SwipeDirection.RIGHT:
            switch_workspace(self.conf, "next")
