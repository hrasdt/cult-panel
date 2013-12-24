from gi.repository import Clutter, Wnck
import arrow

from PagerModel import PagerModel, get_pager_model, workspace_by_number
from PagerModel import is_skipped_tasklist, is_mini, is_urgent, is_active, is_normal

def new_pixbuf_texture(ww, hh, pb):
    t = Clutter.Texture.new()
    
    # Set dimensions.
    t.set_width(ww)
    t.set_height(hh)
    
    # Set pixel data.
    t.set_from_rgb_data(
        pb.get_pixels(),
        pb.props.has_alpha,
        pb.get_width(), pb.get_height(),
        pb.get_rowstride(),
        4 if pb.props.has_alpha else 3, 0)
    return t

class TaskbarItem(Clutter.Box):
    def __init__(self, window, conf, height = 16):
        Clutter.Box.__init__(self)

        self.conf = conf

        # The window is a WnckWindow.
        self.wnck_win = window

        self.lm = Clutter.BoxLayout.new()
        self.lm.set_spacing(height / 4)
        self.set_layout_manager(self.lm)

        # Get the icon.
        if conf.getboolean("Taskbar", "show-icons"):
            self.icon = new_pixbuf_texture(height, height,
                                           window.get_icon())
        else:
            self.icon = None

        # And the text label.
        fontspec = conf.get("Taskbar", "font-name") + " " + conf.get("Taskbar", "font-size")
        self.label = Clutter.Text.new_full(fontspec,
                                           window.get_name(),
                                           conf.getcolour("Taskbar",
                                                          "font-colour"))
        if conf.getboolean("Taskbar", "fixed-width"):
            if self.icon:
                if self.label:
                    self.label.set_size(conf.getint("Taskbar", "width") - self.icon.get_width() - self.lm.get_spacing(), -1)
            else:
                if self.label:
                    self.label.set_size(conf.getint("Taskbar", "width"), -1)
        
        # Add the parts.
        if conf.getboolean("Taskbar", "show-icons"):
            self.add_actor(self.icon)
        if conf.getboolean("Taskbar", "show-labels"):
            self.add_actor(self.label)

        # Hook up input.
        self.set_reactive(True)
        self.connect("button-press-event",
                     self.press_event)

        # And connect signals.
        self.wnck_win.connect("icon-changed", self.icon_changed)
        self.wnck_win.connect("name-changed", self.name_changed)
        self.wnck_win.connect("workspace-changed", self.workspace_changed)

        self.wnck_win.connect("state-changed", self.state_changed)

    def belongs_to(self, window):
        return window is self.wnck_win

    def get_window(self):
        return self.wnck_win
    
    def press_event(self, actor, event):
        if event.button == 3:
            # Minimise.
            self.wnck_win.minimize()

        elif event.button == 2:
            # Close.
            self.wnck_win.close(arrow.now().timestamp)
        
        elif event.button == 1:
            # Or raise.
            self.wnck_win.activate(arrow.now().timestamp)

    def name_changed(self, win):
        self.label.set_text(win.get_name())

    def icon_changed(self, win):
        """ Update the icon to reflect a change. """
        self.icon = new_pixbuf_texture(self.icon.get_width(),
                                       self.icon.get_height(),
                                       win.get_icon())

    def state_changed(self, win, change_mask, new_state):
        self.update_colour()
    
    def update_colour(self):
        col = None
        if is_urgent(self.wnck_win):
            col = self.conf.getcolour("Taskbar", "urgent")
        elif is_mini(self.wnck_win):
            col = self.conf.getcolour("Taskbar", "minimised")
        elif is_active(self.wnck_win):
            col = self.conf.getcolour("Taskbar", "active")
        elif is_normal(self.wnck_win):
            col = self.conf.getcolour("Taskbar", "normal")
        self.set_color(col)
                    
    def workspace_changed(self, win):
        """ Update the workspace that this window is on. """
        # The parent must be a Taskbar.
        self.get_parent().window_workspace_changed(win, self)

class Taskbar(Clutter.Box):
    def __init__(self, conf, screen, size):
        Clutter.Box.__init__(self)
        active_ws = screen.get_active_workspace()

        self.screen = screen
        self.conf = conf
        self.panel_size = size

        self.lm = Clutter.BoxLayout()
        self.lm.set_spacing(2)
        self.set_layout_manager(self.lm)

        # Work out the orientation/size.
        if self.conf.is_vertical():
            self.lm.set_vertical(True)
            
        for w in get_pager_model().get_tasklist(None, True):
            item = TaskbarItem(w, self.conf, height = min(*size))
            self.set_visibility(item, [None, active_ws])
            item.update_colour()
            self.add_actor(item)
        
        # Make sure the right windows are visible.
        self.refresh()

        # And connect the signals.
        screen.connect("active-workspace-changed", self.active_workspace_changed)
        screen.connect("window-opened", self.add_window)
        screen.connect("window-closed", self.remove_window)
        screen.connect("active-window-changed", self.update_active_window)

    def set_visibility(self, task_item, dat):
        """ Set the correct visibility for a TaskbarItem. """
        prev, cur = dat
        
        window = task_item.wnck_win
        ws = window.get_workspace()
            
        # Never show these.
        if is_skipped_tasklist(window):
            task_item.hide()

        # Always show in this case.
        elif self.conf.getboolean("Taskbar", "all-workspaces"):
            task_item.show()

        # Sticky window, but not skip-tasklist.
        elif ws is None:
            task_item.show()

        # It was on the last one; hide it!
        elif ws is prev:
            task_item.hide()

        # Nope; we need to show this now.
        elif ws is cur:
            task_item.show()

        else:
            task_item.hide()
        
    def refresh(self):
        self.active_workspace_changed(None, None)
        
    def active_workspace_changed(self, screen, prev):
        cur = Wnck.Screen.get_default().get_active_workspace()
        
        self.foreach(self.set_visibility, [prev, cur])

    def add_window(self, screen, window):
        item = TaskbarItem(window, self.conf, height = min(*self.panel_size))
        self.set_visibility(item, [None, screen.get_active_workspace()])
        self.add_actor(item)

    def remove_window(self, screen, window):
        """ Remove an item from the taskbar completely.

        This will be called when a window is closed.
        """
        def do_remove(task, dat = None):
            if task.belongs_to(window):
                self.remove_actor(task)

        self.foreach(do_remove, None)

    def update_active_window(self, screen, prev):
        cur = self.screen.get_active_window()
        did_change = 0
        
        for i in self.get_children():
            if did_change >= 2: return
            if i.belongs_to(prev) or i.belongs_to(cur):
                did_change += 1
                i.update_colour()
                
    def window_workspace_changed(self, window, taskbar_child):
        if window.get_workspace() != self.screen.get_active_workspace():
            taskbar_child.hide()
        else:
            taskbar_child.show()
