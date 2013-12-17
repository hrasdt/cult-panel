from gi.repository import Gtk, Wnck, Gdk, GdkPixbuf

import arrow
import config

class TasklistItem(Gtk.Button):
    def __init__(self, wnckwin, width = 100, height = 16):
        Gtk.Button.__init__(self)

        # Store the Wnck window.
        self.win = wnckwin

        # Get the icon and name from the Wnck window.
        pix = self.win.get_icon()
        # Scale the pixbuf.
        scaling = (height - 2) / pix.get_height()
        pix = pix.scale_simple(pix.get_width() * scaling,
                               height - 2,
                               GdkPixbuf.InterpType.BILINEAR)
        
        self.icon = Gtk.Image.new_from_pixbuf(pix)
        self.name = self.win.get_name()

        self.set_image(self.icon)
        self.set_label(self.name)

        # Set style.
        self.set_relief(Gtk.ReliefStyle.NONE)

        # Size.
        self.set_size_request(100, height)

        # Connect signals.
        self.connect("clicked", self.selected)


    def selected(self, widget, data = None):
        """ The button was selected (with a left click)"""
        ts = arrow.now().timestamp
        self.win.unminimize(ts)
        self.win.activate(ts)

class Tasklist(Gtk.Box):
    def __init__(self, windows, current_workspace, conf):
        Gtk.Box.__init__(self)
        self.windows = windows
        self.widgets = {}

        self.config = conf

        # Create widgets for all the windows.
        for i in self.windows:
            # Add it to the list.
            self.widgets[i] = TasklistItem(i, 16)
            self.pack_start(self.widgets[i], False, False, 2)

        # Make sure the proper windows are displayed.
        self.refresh(current_workspace)

    def refresh(self, workspace):
        active = list(self.config.get_scalar("window-list.active")) + [1.]
        mini = list(self.config.get_scalar("window-list.minimised")) + [1.]
        normal = list(self.config.get_scalar("window-list.normal")) + [1.]

        for win in self.windows:
            if win.get_workspace() == workspace:
                self.widgets[win].show()
                if win.is_active():
                    self.widgets[win].override_background_color(Gtk.StateType.NORMAL,
                                                                Gdk.RGBA(*active))
                elif win.is_minimized():
                    self.widgets[win].override_background_color(Gtk.StateType.NORMAL,
                                                                Gdk.RGBA(*mini))
                else:
                    self.widgets[win].override_background_color(Gtk.StateType.NORMAL,
                                                                Gdk.RGBA(*normal))
            else:
                self.widgets[win].hide()

    def handle_events(self, win, screen, typeof = ""):
        # Handle destroy/create events.
        if typeof == "window-closed":
            try:
                self.widgets[win].destroy()
                del self.widgets[win]
                self.windows.remove(win)

            # We didn't know about that one.
            # Ignore it.
            except KeyError as er:
                pass
            except ValueError as er:
                pass
            
        elif typeof == "window-opened":
            self.windows.append(win)
            self.widgets[win] = TasklistItem(win, 16)
            self.pack_start(self.widgets[win], False, False, 2)
        
        self.refresh(screen.get_active_workspace())
