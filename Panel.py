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
        # MAIN_BOX is the container for the three important layout widgets:
        # - box_start, box_middle, box_end
        # each of which will hold the taskbar/clock/pager/etc.
        MAIN_BIN = Clutter.BinLayout.new(Clutter.BinAlignment.CENTER,
                                         Clutter.BinAlignment.CENTER)
        MAIN_BOX = Clutter.Box.new(MAIN_BIN)
        MAIN_BOX.set_size(*self.size)
        self.stage.add_actor(MAIN_BOX)

        # Add them.
        box_start_lo = Clutter.BoxLayout.new()
        box_start_lo.set_spacing(4)
        box_middle_lo = Clutter.BoxLayout.new()
        box_middle_lo.set_spacing(4)
        box_end_lo = Clutter.BoxLayout.new()
        box_end_lo.set_spacing(4)

        # Be vertical if necessary.
        START = Clutter.BinAlignment.START
        MID = Clutter.BinAlignment.CENTER
        END = Clutter.BinAlignment.END

        v = conf.is_vertical()
        if v:
            box_start_lo.set_vertical(True)
            box_middle_lo.set_vertical(True)
            box_end_lo.set_vertical(True)

        # And the boxes.
        self.box_start = Clutter.Box.new(box_start_lo)
        MAIN_BIN.add(self.box_start, [START, MID][v], [MID, START][v])
        self.box_middle = Clutter.Box.new(box_middle_lo)
        MAIN_BIN.add(self.box_middle, MID, MID)
        self.box_end = Clutter.Box.new(box_end_lo)
        MAIN_BIN.add(self.box_end, [END, MID][v], [MID, END][v])

        # Parse the config string.
        try:
            start, mid, end = conf.get("Panel", "order").split("|", 2)

            # Now, work out which goes where.
            self.add_widgets(start, self.box_start)
            self.add_widgets(mid, self.box_middle)
            self.add_widgets(end, self.box_end)

        except ValueError as e:
            print("Incorrect order specification: "
                  "got {}.".format(conf.get("Panel", "order")))
            sys.exit(-1)
        
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

    def add_widgets(self,
                   widgetlist,
                   box):
        """ Add a list of widgets to one of our locations.

        Position should be one of the Clutter.Boxes.
        This function automatically adjusts for vertical/horizontal layouts.
        """
        # widgetlist is a string.
        for x in widgetlist:
            q = None
            if x == "t": # Taskbar.
                q = Taskbar(self.conf, self.size)

            elif x == "p": # Pager.
                q = Pager(self.conf)

            elif x == "b": # Battery.
                q = BatteryApplet(self.conf)

            elif x == "c": # Clock.
                q = ClockApplet(self.conf)

            if q:
                box.add_actor(q)
            else:
                print("Unknown applet identifier " + x)

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
