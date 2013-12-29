from gi.repository import Clutter, Wnck, GObject
import arrow

def is_skipped_pager(win):
    return win.is_skip_pager()

def is_skipped_tasklist(win):
    return win.is_skip_tasklist()

def is_mini(win):
    return win.is_minimized()

def is_urgent(win):
    return win.needs_attention()

def is_active(win):
    return win.is_active()

def is_normal(win):
    return not (is_urgent(win) or is_mini(win) or is_active(win))

def switch_workspace(conf, direction):
    screen = conf.getscreen()
    
    cur = screen.get_active_workspace()
    num = screen.get_workspace_count()

    if direction == "next":
        target = screen.get_workspace( (cur.get_number() + 1) % num)
        target.activate(arrow.now().timestamp)
    elif direction == "prev":
        target = screen.get_workspace( (cur.get_number() - 1) % num)
        target.activate(arrow.now().timestamp)

class PagerModel (GObject.GObject):
    """ Store the state of workspaces. """

    # Constants for the state bitstring.
    NO_WINDOWS = 0 #
    MINIMISED  = 1 # Minimised window.
    OCCUPIED   = 2 # A normal window.
    URGENT     = 4 # Window requesting attention.
    ACTIVE     = 8 # The active workspace.

    # Add signals so we can communicate changes.
    __gsignals__ = {
        "update-pager": (GObject.SIGNAL_RUN_FIRST, None,
                         (Wnck.Workspace,)), # Arguments.
    }

    def __init__(self, conf):
        GObject.GObject.__init__(self)
        
        self.screen = conf.getscreen()

        # Create the list of workspaces.
        self.workspaces = [] # List of WnckWorkspaces
        self.workspace_states = {} # Map from ^^ to a state bitmask.
        self.tasklist = {} # A map from WnckWorkspaces to a list of the windows they contain.
        
        self.refresh_everything()

        # Connect events.
        self.screen.connect("active-workspace-changed", self.change_workspace)
        self.screen.connect("window-opened", self.add_window)
        self.screen.connect("window-closed", self.remove_window)

    def refresh_everything(self, *ignored):
        self.workspaces = self.screen.get_workspaces()
        self.workspace_states = {ws : PagerModel.NO_WINDOWS
                                 for ws in self.workspaces}

        self.tasklist = {ws: [] for ws in self.workspaces} # Clear the tasklist.
        self.tasklist[None] = [] # Sticky windows live here.
        
        win_list = self.screen.get_windows()
        for w in win_list:
            self.add_window(None, w)

        # Set the active workspace.
        a = self.screen.get_active_workspace()
        if a is not None:
            self.workspace_states[a] |= PagerModel.ACTIVE

    def change_workspace(self, screen, prev):
        # Disable the 'active' flag on the old workspace.
        self.workspace_states[prev] &= ~PagerModel.ACTIVE

        # And enable it on the now-current one.
        cur = self.screen.get_active_workspace()
        self.workspace_states[cur] |= PagerModel.ACTIVE

        self.emit("update-pager", cur)

    def window_workspace_changed(self, win):
        workspace = win.get_workspace()

        # Remove it from whereever it was before now.
        for w in [None] + self.workspaces:
            # It used to be here.
            if win in self.tasklist[w]:
                self.tasklist[w].remove(win)
                self.recalculate_workspace_state(w)

        if workspace is not None:
            self.tasklist[workspace].append(win)
        
        self.recalculate_workspace_state(workspace)

    def add_window(self, screen, win):
        workspace = win.get_workspace()
        
        # Update the tasklist.
        if not is_skipped_tasklist(win):
            self.tasklist[workspace].append(win)
            # Connect the signals.
            win.connect("workspace-changed", self.window_workspace_changed)
            win.connect("state-changed",
                        lambda w,*_: self.recalculate_workspace_state(w.get_workspace()))
        
        self.recalculate_workspace_state(workspace)
        self.emit("update-pager", workspace)
    
    def remove_window(self, screen, win):
        """ Remove a window from the pager (e.g. if it's closed). """
        workspace = win.get_workspace()

        # Remove the window from every workspace list it might be in.
        for k in self.tasklist:
            if win in self.tasklist[k]:
                self.tasklist[k].remove(win)
            self.recalculate_workspace_state(k)

        self.emit("update-pager", ws)
        
    def recalculate_workspace_state(self, workspace=None):
        if workspace is None: #isinstance(workspace, int) and workspace == -1:
            for i in self.workspaces:
                self.recalculate_workspace_state(i)

        elif workspace is not None:
            active = self.screen.get_active_workspace()
            
            if workspace is active:
                self.workspace_states[workspace] = PagerModel.ACTIVE
            else:
                self.workspace_states[workspace] = PagerModel.NO_WINDOWS

            for win in self.tasklist[workspace]:
                # Now, update the Pager.
                if is_skipped_pager(win):
                    # We ignore these for obvious reasons.
                    if not is_urgent(win):
                        continue
                    # But if it's urgent, it should show regardless.
                    else:
                        self.workspace_states[workspace] |= PagerModel.URGENT
                else:
                    # Minimised.
                    if is_mini(win):
                        self.workspace_states[workspace] |= PagerModel.MINIMISED
                        # Just a normal window.
                    else:
                        self.workspace_states[workspace] |= PagerModel.OCCUPIED

            self.emit("update-pager", workspace)
                    
    def get_state(self, ws):
        """ Get the state bitmask for a workspace. """
        return self.workspace_states[ws]
        
    def get_state_list(self):
        return [self.workspace_states[i] for i in self.workspaces]
        
    def get_workspace_number(self, num):
        return self.workspaces[num]

    def get_tasklist(self, workspace, all_workspaces = False):
        if all_workspaces or workspace is None:
            return [task for ws in self.workspaces for task in self.tasklist[ws]]
        else:
            if isinstance(workspace, int):
                return self.tasklist[self.workspaces[workspace]]
            else:
                return self.tasklist[workspace]

    def list_windows(self, workspace):
        ret = ""
        ret += workspace.get_name() + ": " + ", ".join(w.get_name() for w in self.tasklist[workspace]) + "\n"
        return ret
