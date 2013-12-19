from gi.repository import Clutter, Wnck
import arrow
from PagerModel import PagerModel, get_pager_model, workspace_by_number

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
    FONT_SPEC = "Bauhaus 9"
    TEXT_COLOUR = Clutter.Color.from_string("#fff")[1]
    
    def __init__(self, window, height = 16, width = 140):
        Clutter.Box.__init__(self)

        # Set the width.
        self.preferred_width = width
        
        # The window is a WnckWindow.
        self.wnck_win = window

        self.lm = Clutter.BoxLayout.new()
        self.lm.set_spacing(height / 4)
        self.set_layout_manager(self.lm)

        # Get the icon.
        self.icon = new_pixbuf_texture(height, height,
                                       window.get_icon())

        # And the text label.
        self.label = Clutter.Text.new_full(self.FONT_SPEC,
                                           window.get_name(),
                                           self.TEXT_COLOUR)
        if width > 0:
            self.label.set_size(width - self.icon.get_width() - self.lm.get_spacing(), -1)
        
        # Add the parts.
        self.add_actor(self.icon)
        self.add_actor(self.label)

        # Hook up input.
        self.set_reactive(True)
        self.connect("button-press-event",
                     self.press_event)

        # And connect signals.
        self.wnck_win.connect("icon-changed", self.icon_changed)
        self.wnck_win.connect("name-changed", self.name_changed)
        self.wnck_win.connect("state-changed", self.state_changed)
        self.wnck_win.connect("workspace-changed", self.workspace_changed)

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
        self.set_color(Taskbar.get_theme_colour(win))
                    
    def workspace_changed(self, win):
        """ Update the workspace that this window is on. """
        # The parent must be a Taskbar.
        self.get_parent().window_workspace_changed(win, self)

class Taskbar(Clutter.Box):
    def __init__(self, all_workspaces = False):
        Clutter.Box.__init__(self)
        
        self.show_all_workspaces = all_workspaces

        self.lm = Clutter.BoxLayout()
        self.lm.set_spacing(2)
        self.set_layout_manager(self.lm)

        for w in get_pager_model().get_tasklist(None):
            item = TaskbarItem(w)
            self.add_actor(item)
        
        # Make sure the right windows are visible.
        self.refresh()

        # And connect the signals.
        scr = Wnck.Screen.get_default()
        scr.connect("active-workspace-changed", self.refresh)

    def refresh(self, screen = None, prev = None):
        if self.show_all_workspaces:
            # We just show everything.
            self.show_all()
        else:
            cur = Wnck.Screen.get_default().get_active_workspace()
            wins = get_pager_model().get_tasklist(cur, False)
            self.foreach(
                lambda win,_: win.show() if win.wnck_win in wins else win.hide(),
                None
                )

    def window_workspace_changed(self, window, taskbar_child):
        if window.get_workspace() != Wnck.Screen.get_default().get_active_workspace():
            taskbar_child.hide()
        else:
            taskbar_child.show()
            
    def get_theme_colour(window):
        maps = {
            "active": "#404040",
            "minimised": "#0f0f0f",
            "normal": "#303030",
            "urgent": "#505050",
            }
        if window.needs_attention():
            return Clutter.Color.from_string(maps["urgent"])[1]
        elif window.is_minimized():
            return Clutter.Color.from_string(maps["minimised"])[1]
        elif window.is_active():
            return Clutter.Color.from_string(maps["active"])[1]
        else:
            return Clutter.Color.from_string(maps["normal"])[1]