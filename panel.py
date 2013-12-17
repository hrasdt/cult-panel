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
from gi.repository import Gtk, Wnck, Gdk, GObject
import cairo
import arrow # For time mangling.

import config # My config file handler.
from window_list import TasklistItem, Tasklist

# Smooth scroll threshold which will be considered a workspace-changing scroll.
SMOOTH_THRESHOLD = 0.8

class WorkspaceIndicator(Gtk.DrawingArea):
    NO_WINDOWS = ""
    MINIMISED  = "m" # Minimised window.
    OCCUPIED   = "o" # A normal window.
    URGENT     = "u" # Window requesting attention.
    ACTIVE     = "a" # The active workspace.

    DOT_SIZE = 8
    DOT_SPACING = 4

    def __init__(self, screen, height, style = None):
        Gtk.DrawingArea.__init__(self)

        self.screen = screen

        # GTK style information, so we can use CSS.
        self.style = style

        ws = get_used_workspaces(self.screen)
        self.workspace_count = len(ws)
        
        self.set_size_request(self.DOT_SIZE * len(ws) + self.DOT_SPACING * (len(ws) + 1),
                              height)

        # Events and suchlike.
        E = Gdk.EventMask
        self.set_events(E.BUTTON_PRESS_MASK | E.BUTTON_RELEASE_MASK
                        | E.SCROLL_MASK | E.SMOOTH_SCROLL_MASK)
        self.connect("draw", self.draw)
        
    def centre_me(self, widget, allocation, *args):
        self.min_width = self.workspace_count * (self.DOT_SPACING + self.DOT_SIZE) + self.DOT_SPACING

    def draw(self, widget, cr):
        # Draw the dots at the correct place.
        states = get_used_workspaces(self.screen)
        pos = self.DOT_SIZE
                
        for ind, state in enumerate(states):
            self.draw_workspace_indicator(cr, (pos, self.DOT_SIZE), state)
            pos += self.DOT_SIZE + self.DOT_SPACING

    def draw_workspace_indicator(self, cr, position, style, size = 8):
        """ Draw a workspace indicator at the given position.

        Indicators are anchored in the centre.
        Style is a number in [0, 4] which corresponds to [no windows, minimised windows, occupied workspace, urgent, active].
        """
        cr.move_to(*position)

        # Extract appropriate colours.
        if self.style:
            WS_NONE = self.style.get_scalar("indicator.none")
            WS_ACTIVE = self.style.get_scalar("indicator.active")
            WS_URGENT = self.style.get_scalar("indicator.urgent")
            WS_MINIMISED = self.style.get_scalar("indicator.minimised")
            WS_OCCUPIED = self.style.get_scalar("indicator.occupied")

        else:
            WS_NONE = WS_ACTIVE = WS_URGENT = WS_MINIMISED = WS_OCCUPIED = col("dark-grey")
                
        # Do things based on style.
        point = cr.get_current_point()
        def box(colour,
                centre_x = point[0],
                centre_y = point[1],
                w = size, h = size):
            cr.set_source_rgb(*colour)
            cr.rectangle(centre_x - (w / 2), centre_y - (h / 2), w, h)
            cr.fill()
        
        if style == WorkspaceIndicator.NO_WINDOWS \
          or style == WorkspaceIndicator.ACTIVE:
            box(WS_NONE)
        if WorkspaceIndicator.URGENT in style:
            box(WS_URGENT)
        elif WorkspaceIndicator.OCCUPIED in style:
            box(WS_OCCUPIED)
        elif WorkspaceIndicator.MINIMISED in style:
            box(WS_MINIMISED)

        if WorkspaceIndicator.ACTIVE in style:
            box(WS_ACTIVE,
                centre_y = point[1] + size - 2,
                h = 2)
        
    def render_text(self, cr,
                    text, pos,
                    
                    colour = (0.0, 0.0, 0.0),
                    font_face = "DejaVu Sans",
                    font_size = 16,
                    font_weight = cairo.FONT_WEIGHT_NORMAL):

        if colour:
             cr.set_source_rgb(*colour)
        if font_face:
                cr.select_font_face(font_face,
                                    cairo.FONT_SLANT_NORMAL,
                                    font_weight)
        cr.set_font_size(font_size)

        cr.move_to(*pos)
        cr.show_text(text)

def switch_workspace(screen, direction):
    cur = screen.get_active_workspace()
    num = screen.get_workspace_count()

    if direction == "next":
        target = screen.get_workspace( (cur.get_number() + 1) % num)
        target.activate(arrow.now().timestamp)
    elif direction == "prev":
        target = screen.get_workspace( (cur.get_number() - 1) % num)
        target.activate(arrow.now().timestamp)

def get_used_workspaces(screen):
    """ Get a list of active workspaces.

    This returns a string representing the state of all windows.
    Symbols are defined in WorkspaceIndicator.
    
    Windows for which skip-tasklist/pager are set will not be counted, unless they're also marked "urgent".
    """
    
    windows = screen.get_windows()
    workspaces = screen.get_workspaces()
    ret = [WorkspaceIndicator.NO_WINDOWS] * len(workspaces)

    # Lookup for workspace -> index
    ws_keys = {ws: ind for ind, ws in enumerate(workspaces)}

    # Local function.
    def is_skipped(win):
        return win.is_skip_tasklist() or win.is_skip_pager()

    # Set the currently active workspace.
    ret[ws_keys[screen.get_active_workspace()]] = WorkspaceIndicator.ACTIVE
    
    # Now, iterate over the windows, calculating appropriate values for ret.
    for win in windows:
        try:
            key = ws_keys[win.get_workspace()]
        except KeyError as e:
            if e.args[0] == None:
                # This occurs when a window is stickied to every workspace.
                # Then, Wnck returns None/NULL as the workspace.
                continue
            else:
                raise e
        
        if win.needs_attention():
            ret[key] += WorkspaceIndicator.URGENT
        elif not is_skipped(win) and not win.is_minimized():
            ret[key] += WorkspaceIndicator.OCCUPIED
        elif not is_skipped(win) and win.is_minimized():
            ret[key] += WorkspaceIndicator.MINIMISED

    return ret

class ClockApp(Gtk.Label):
    def __init__(self, tformat):
        Gtk.Label.__init__(self)
        self.format = tformat
        self.timer_id = GObject.timeout_add_seconds(1, self.refresh, None)
        self.refresh()
        
    def refresh(self, *args):
        # We use Arrow to work out time.
        now = arrow.now()
        if self.format == "human":
            self.set_text(now.humanize())
        else:
            self.set_text(now.format(self.format))

        # Ensure the timer repeats.
        self.timer_id = GObject.timeout_add_seconds(1, self.refresh, None)

def scroll_workspace_container(child):
    def scroll_cb(w, ev, d = None):
        if ev.type != Gdk.EventType.SCROLL:
            return
        
        elif ev.direction == Gdk.ScrollDirection.SMOOTH\
          and not (-SMOOTH_THRESHOLD < ev.delta_y < SMOOTH_THRESHOLD):
            switch_workspace(screen,
                             "next" if ev.delta_y <= -1 else\
                             "prev" if ev.delta_y >= 1 else\
                             None)
        else:
            if ev.direction in (Gdk.ScrollDirection.DOWN,
                                Gdk.ScrollDirection.LEFT):
                switch_workspace(screen, "prev")
            elif ev.direction in (Gdk.ScrollDirection.UP,
                                  Gdk.ScrollDirection.RIGHT):
                switch_workspace(screen, "next")

    eb = Gtk.EventBox.new()
    eb.add(child)

    eb.add_events(Gdk.EventMask.SCROLL_MASK | Gdk.EventMask.SMOOTH_SCROLL_MASK)
    eb.connect("scroll-event", scroll_cb)

    eb.set_size_request(*child.get_size_request())
    
    return eb

if __name__ == "__main__":
    Gtk.init(sys.argv)

    cstyle = config.load_style("/home/ryan/.config/cultpanel/theme.cfg")

    # Load the screen.
    screen = Wnck.Screen.get_default()
    screen.force_update()
        
    indic = WorkspaceIndicator(screen, height=16, style = cstyle)

    def exit_cb(*args):
        global screen # Capture scope.
        screen = None
        indic.screen = None
        
        Wnck.shutdown()
        Gtk.main_quit()
    
    win = Gtk.Window.new(Gtk.WindowType.TOPLEVEL)
    win.set_name("cult panel")
    win.connect("destroy", exit_cb)

    # Set up state.
    win.set_title("cult panel")
    win.stick()
    win.set_decorated(False)
    win.set_skip_pager_hint(True)
    win.set_skip_taskbar_hint(True)
    win.set_type_hint(Gdk.WindowTypeHint.DOCK)
    win.move(0, 0)

    # The window needs several containers for widgets.
    fixer = Gtk.Fixed()
    win.add(fixer) # Fuck, I hate Gtk's layout.
    
    # Capture events.
    def scroll_cb(w, ev, d = None):
        if ev.type != Gdk.EventType.SCROLL:
            return
        
        elif ev.direction == Gdk.ScrollDirection.SMOOTH\
          and not (-SMOOTH_THRESHOLD < ev.delta_y < SMOOTH_THRESHOLD):
            switch_workspace(screen,
                             "next" if ev.delta_y <= -1 else\
                             "prev" if ev.delta_y >= 1 else\
                             None)
        else:
            if ev.direction in (Gdk.ScrollDirection.DOWN,
                                Gdk.ScrollDirection.LEFT):
                switch_workspace(screen, "prev")
            elif ev.direction in (Gdk.ScrollDirection.UP,
                                  Gdk.ScrollDirection.RIGHT):
                switch_workspace(screen, "next")

    evbox = Gtk.EventBox.new()
    evbox.set_size_request(1366, 16) # Fill the panel.
    evbox.add_events(Gdk.EventMask.SCROLL_MASK|Gdk.EventMask.SMOOTH_SCROLL_MASK)
    evbox.connect("button_press_event",
                  lambda w, ev, d = None: switch_workspace(screen, "next" if ev.button == 1 else "prev" if ev.button == 3 else None))

    evbox.connect("scroll_event",
                  scroll_cb)
    win.connect("scroll_event",
                scroll_cb)
    
    fixer.put(evbox, 0, 0)
    
    # A container for normal, well-behaved widgets.
    box = Gtk.Box()
    box.set_size_request(1366, 16)
#    box.set_column_homogeneous(False)
    box.set_hexpand(True)
#    fixer.put(box, 0, 0)
    evbox.add(box)

    tasklist = Tasklist(screen.get_windows(),
                        screen.get_active_workspace(),
                        cstyle)
    box.pack_start(tasklist, False, False, 0)
    
    # Update the workspace indicator.
    def ws_event(screen, window, typeof = None):

        if typeof in ("window-opened",
                      "window-closed",
                      "workspace-created",
                      "workspace-destroyed",
                      "active-window-changed",
                      "active-workspace-changed"):
            # We want to redraw the indicators.
            indic.queue_draw()

        # Don't update the tasklist in this case.
        if typeof == "active-window-changed"\
          and window == None:
            return

        # And update the tasklist.
        tasklist.handle_events(window, screen, typeof)

    for ev in ["window-opened",
               "window-closed",
               "workspace-created",
               "workspace-destroyed",
               "active-window-changed",
               "active-workspace-changed"]:
        screen.connect(ev, ws_event, ev)

    # The clock widget.
    clock = ClockApp(cstyle.clock_format)
    box.pack_end(clock, False, False, 0)
    #box.attach_next_to(clock, None, Gtk.PositionType.RIGHT, 1, 1)

    # We want to force the workspace dots to always be centred on-screen.
    # GTK+ does not make this an easy thing, although understandably so.
    aligner = Gtk.Alignment.new(0.5, 0.5, 0.0, 0.0)
    aligner.set_size_request(1366, 16)
    aligner.set_hexpand(True)
    aligner.set_vexpand(True)
    aligner.add(indic) # Add the indicator to the aligner.
    fixer.put(aligner, 0, 0) # Also put this at the top-left.

    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(),
                                             cstyle.gstyle,
                                             Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    win.show_all()

    try:
        Gtk.main()
    except KeyboardInterrupt as er:
        exit_cb()
