from gi.repository import Wnck, Clutter, Gdk
import arrow

from PagerModel import PagerModel, switch_workspace, get_pager_state, workspace_by_number

class PagerDot(Clutter.Box):
    def __init__(self, conf, workspace, pager_model):
        Clutter.Box.__init__(self)

        self.conf = conf
        self.pager_model = pager_model

        # The workspace name.
        self.set_name(workspace.get_name())
        self.workspace = workspace

        self.lm = Clutter.BinLayout.new(Clutter.BinAlignment.CENTER,
                                        Clutter.BinAlignment.CENTER)
        self.set_layout_manager(self.lm)

        # Stylin'
        size = conf.getint("Pager", "size")
        self.main_dot = Clutter.Rectangle.new()
        self.main_dot.set_size(size, size)

        self.active_dot = Clutter.Rectangle.new()
        self.active_dot.set_size(size, size / 4)

        self.update()

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
        state = self.pager_model.get_state(self.workspace)

        # Set the colours.
        col = None
        if state & PagerModel.URGENT:
            col = self.conf.getcolour("Pager", "urgent")
        elif state & PagerModel.OCCUPIED:
            col = self.conf.getcolour("Pager", "occupied")
        elif state & PagerModel.MINIMISED:
            col = self.conf.getcolour("Pager", "minimised")
        elif (state & ~PagerModel.ACTIVE) == PagerModel.NO_WINDOWS:
            col = self.conf.getcolour("Pager", "none")

        self.main_dot.set_color(col)

        if state & PagerModel.ACTIVE:
            self.active_dot.set_color(self.conf.getcolour("Pager", "active"))
        else:
            self.active_dot.set_color(Clutter.Color.from_string("#0000")[1])

    def click(self, actor, event):
        if event.button == 1:
            self.workspace.activate(arrow.now().timestamp)

class Pager(Clutter.Box):
    """ A pager widget to show the workspace view. """
    def __init__(self, conf, pager_model):
        Clutter.Box.__init__(self)

        self.conf = conf
        self.dot_spacing = conf.getint("Pager", "size") / 2

        self.lm = Clutter.BoxLayout.new()
        self.lm.set_spacing(self.dot_spacing)
        self.set_layout_manager(self.lm)

        for i in pager_model.workspaces:
            indic = PagerDot(conf, i, pager_model)
            self.add_actor(indic)

        # Connect signals.
        screen = conf.getscreen()
        screen.connect("active-workspace-changed", self.update)
        screen.connect("window-opened", self.update)
        screen.connect("window-closed", self.update)

    def update(self, *ignored):
        """ Update the display of all the workspaces. """
        # Call update on each child with the appropriate workspace state.
        self.foreach(PagerDot.update, None)
