from gi.repository import Wnck, Clutter, Gdk

from wmanagement import Workspace, switch_workspace, get_used_workspaces

class PagerDot(Clutter.Box):
    def __init__(self, workspace, height = 16):
        Clutter.Box.__init__(self)

        # The Workspace object.
        self.workspace = workspace
        
        # The workspace name.
        self.set_name(self.workspace.name)
        self.state = self.workspace.state

        self.lm = Clutter.BinLayout.new(Clutter.BinAlignment.CENTER,
                                        Clutter.BinAlignment.CENTER)
        self.set_layout_manager(self.lm)

        # Stylin'
        self.main_dot = Clutter.Rectangle.new()
        self.main_dot.set_size(height, height)
        self.main_dot.set_color(Pager.get_colour(self.workspace.state, "main"))

        self.active_dot = Clutter.Rectangle.new()
        self.active_dot.set_size(height, height / 4)
        self.active_dot.set_color(Pager.get_colour(self.workspace.state, "active"))
 
        self.lm.add(self.main_dot,
                    Clutter.BinAlignment.CENTER, Clutter.BinAlignment.CENTER)
        self.lm.add(self.active_dot,
                    Clutter.BinAlignment.CENTER, Clutter.BinAlignment.END)

    def update(self, workspace_list):
        # Parse the workspace list.
        name = self.get_name()

        ws = [x for x in workspace_list if x.name == name][0]
        self.state = ws.state
        self.main_dot.set_color(Pager.get_colour(self.state, "main"))
        self.active_dot.set_color(Pager.get_colour(self.state, "active"))

class Pager(Clutter.Box):
    DOT_SIZE = 8
    DOT_SPACING = 4

    def __init__(self, workspaces, height = 16):
        Clutter.Box.__init__(self)

        self.lm = Clutter.BoxLayout.new()
        self.lm.set_spacing(self.DOT_SPACING)
        self.set_layout_manager(self.lm)

        if workspaces:
            self.workspaces = workspaces
            for item in workspaces:
                ws = PagerDot(item, self.DOT_SIZE)
                self.add_actor(ws)
                self.added = True
        else:
            self.workspaces = []

    def update(self, workspaces = []):
        """ Update the display of all the workspaces. """
        # Call update on each child with the appropriate workspace state.
        if not self.workspaces: # No workspaces exist.
            self.workspaces = workspaces
            for item in workspaces:
                ws = PagerDot(item, self.DOT_SIZE)
                self.add_actor(ws)
            self.added = True

        else:
            self.foreach(PagerDot.update, workspaces)

    def get_colour(state, element):
        maps = {"none": "#404040",
                "active": "#efefef",
                "urgent": "#ffffff",
                "minimised": "#707070",
                "occupied": "#aaaaaa",
                "blank": "#0000",
                }

        if element == "active":
            if Workspace.ACTIVE in state:
                col = Clutter.Color.from_string(maps["active"])[1]
            else:
                col = Clutter.Color.from_string(maps["blank"])[1]

        else:
            if Workspace.URGENT in state:
                col = Clutter.Color.from_string(maps["urgent"])[1]
            elif Workspace.OCCUPIED in state:
                col = Clutter.Color.from_string(maps["occupied"])[1]
            elif Workspace.MINIMISED in state:
                col = Clutter.Color.from_string(maps["minimised"])[1]
            elif Workspace.NO_WINDOWS in state:
                col = Clutter.Color.from_string(maps["none"])[1]

        return col
