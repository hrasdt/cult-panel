from gi.repository import Wnck, Clutter, Gdk
import arrow

from PagerModel import PagerModel, get_pager_model, switch_workspace, get_pager_state, workspace_by_number

class PagerDot(Clutter.Box):
    def __init__(self, workspace, height = 16):
        Clutter.Box.__init__(self)

        # The workspace name.
        self.set_name(workspace.get_name())
        self.workspace = workspace

        self.lm = Clutter.BinLayout.new(Clutter.BinAlignment.CENTER,
                                        Clutter.BinAlignment.CENTER)
        self.set_layout_manager(self.lm)

        # Stylin'
        self.main_dot = Clutter.Rectangle.new()
        self.main_dot.set_size(height, height)
        self.main_dot.set_color(Pager.get_theme_colour(self.workspace, "main"))

        self.active_dot = Clutter.Rectangle.new()
        self.active_dot.set_size(height, height / 4)
        self.active_dot.set_color(Pager.get_theme_colour(self.workspace, "active"))

        # Add the components.
        self.lm.add(self.main_dot,
                    Clutter.BinAlignment.CENTER, Clutter.BinAlignment.CENTER)
        self.lm.add(self.active_dot,
                    Clutter.BinAlignment.CENTER, Clutter.BinAlignment.END)

        # Connect input & signals.
        self.set_reactive(True)
        self.connect("button-press-event", self.click)

    def update(self, *ignored):
        self.set_name(self.workspace.get_name())

        # Set the colours.
        self.main_dot.set_color(Pager.get_theme_colour(self.workspace, "main"))
        self.active_dot.set_color(Pager.get_theme_colour(self.workspace, "active"))

    def click(self, actor, event):
        if event.button == 1:
            self.workspace.activate(arrow.now().timestamp)

class Pager(Clutter.Box):
    """ A pager widget to show the workspace view. """
    DOT_SIZE = 8
    DOT_SPACING = 4

    def __init__(self, screen, height = 16):
        Clutter.Box.__init__(self)

        self.lm = Clutter.BoxLayout.new()
        self.lm.set_spacing(self.DOT_SPACING)
        self.set_layout_manager(self.lm)

        for i in get_pager_model().workspaces:
            indic = PagerDot(i, self.DOT_SIZE)
            self.add_actor(indic)

        # Connect signals.
        screen.connect("active-workspace-changed", self.update)
        screen.connect("window-opened", self.update)
        screen.connect("window-closed", self.update)

    def update(self, *ignored):
        """ Update the display of all the workspaces. """
        # Call update on each child with the appropriate workspace state.
        self.foreach(PagerDot.update, None)

    def get_theme_colour(workspace, element):
        col = None
        maps = {"none": "#404040",
                "active": "#efefef",
                "urgent": "#ffffff",
                "minimised": "#707070",
                "occupied": "#aaaaaa",
                "blank": "#0000",
                }
        state = get_pager_state(workspace)

        if element == "active":
            if state & PagerModel.ACTIVE:
                col = Clutter.Color.from_string(maps["active"])[1]
            else:
                col = Clutter.Color.from_string(maps["blank"])[1]

        else:
            if state & PagerModel.URGENT:
                col = Clutter.Color.from_string(maps["urgent"])[1]
            elif state & PagerModel.OCCUPIED:
                col = Clutter.Color.from_string(maps["occupied"])[1]
            elif state & PagerModel.MINIMISED:
                col = Clutter.Color.from_string(maps["minimised"])[1]
            elif (state & ~PagerModel.ACTIVE) == PagerModel.NO_WINDOWS:
                col = Clutter.Color.from_string(maps["none"])[1]
            else:
                raise ValueError("Invalid state bitmask " + bin(state))

        return col
