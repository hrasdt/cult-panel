from gi.repository import Wnck, Clutter, Gdk

#from wmanagement import Workspace, switch_workspace, get_used_workspaces
from PagerModel import PagerModel, get_model, switch_workspace, get_state, workspace_by_number

class PagerDot(Clutter.Box):
    def __init__(self, workspace, height = 16):
        Clutter.Box.__init__(self)

        # The workspace name.
        self.set_name(workspace.get_name())
        self.number = workspace.get_number()

        self.lm = Clutter.BinLayout.new(Clutter.BinAlignment.CENTER,
                                        Clutter.BinAlignment.CENTER)
        self.set_layout_manager(self.lm)

        # Stylin'
        self.main_dot = Clutter.Rectangle.new()
        self.main_dot.set_size(height, height)
        self.main_dot.set_color(Pager.get_colour(get_state(self.number), "main"))

        self.active_dot = Clutter.Rectangle.new()
        self.active_dot.set_size(height, height / 4)
        self.active_dot.set_color(Pager.get_colour(get_state(self.number), "active"))
 
        self.lm.add(self.main_dot,
                    Clutter.BinAlignment.CENTER, Clutter.BinAlignment.CENTER)
        self.lm.add(self.active_dot,
                    Clutter.BinAlignment.CENTER, Clutter.BinAlignment.END)

    def update(self, *ignored):
        # Parse the workspace list.
        self.set_name(workspace_by_number(self.number).get_name())
        state = get_state(self.number)

        self.main_dot.set_color(Pager.get_colour(state, "main"))
        self.active_dot.set_color(Pager.get_colour(state, "active"))

class Pager(Clutter.Box):
    DOT_SIZE = 8
    DOT_SPACING = 4

    def __init__(self, height = 16):
        Clutter.Box.__init__(self)

        self.lm = Clutter.BoxLayout.new()
        self.lm.set_spacing(self.DOT_SPACING)
        self.set_layout_manager(self.lm)

        for i in get_model().workspaces:
            indic = PagerDot(i, self.DOT_SIZE)
            self.add_actor(indic)

    def update(self, *ignored):
        """ Update the display of all the workspaces. """
        # Call update on each child with the appropriate workspace state.
        self.foreach(PagerDot.update, None)

    def get_colour(state, element):
        col = None
        maps = {"none": "#404040",
                "active": "#efefef",
                "urgent": "#ffffff",
                "minimised": "#707070",
                "occupied": "#aaaaaa",
                "blank": "#0000",
                }

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
