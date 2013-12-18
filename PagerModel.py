from gi.repository import Clutter, Wnck

def is_skipped(win):
    return win.is_skip_tasklist() or win.is_skip_pager()

def is_mini(win):
    return win.is_minimized()

def is_urgent(win):
    return win.needs_attention()

def switch_workspace(direction):
    screen = Wnck.Screen.get_default()
    
    cur = screen.get_active_workspace()
    num = screen.get_workspace_count()

    if direction == "next":
        target = screen.get_workspace( (cur.get_number() + 1) % num)
        target.activate(arrow.now().timestamp)
    elif direction == "prev":
        target = screen.get_workspace( (cur.get_number() - 1) % num)
        target.activate(arrow.now().timestamp)

_g_model = None
def get_model():
    """ Get a representation of the active workspaces.

    Windows for which skip-tasklist/pager are set will not be counted, unless they're also marked "urgent".
    """
    global _g_model

    if _g_model is None:
        _g_model = PagerModel()

    return _g_model

def get_state(ws):
    return get_model().get_state(ws)

def workspace_by_number(num):
    return get_model().get_workspace_number(num)

class PagerModel (object):
    """ Store the state of workspaces. """

    # Constants for the state bitstring.
    NO_WINDOWS = 0 #
    MINIMISED  = 1 # Minimised window.
    OCCUPIED   = 2 # A normal window.
    URGENT     = 4 # Window requesting attention.
    ACTIVE     = 8 # The active workspace.

    def __init__(self):
        self.screen = Wnck.Screen.get_default()

        # Create the list of workspaces.
        self.workspaces = [] # List of WnckWorkspaces
        self.workspace_states = {} # Map from ^^ to a state bitmask.
        self.refresh_state()

        # Connect events.
        self.screen.connect("active-workspace-changed", self.change_workspace)
        self.screen.connect("window-opened", self.refresh_state)
        self.screen.connect("window-closed", self.refresh_state)

    def refresh_state(self, *ignored):
        self.workspaces = self.screen.get_workspaces()
        self.workspace_states = {ws : PagerModel.NO_WINDOWS
                                 for ws in self.workspaces}
        
        win_list = self.screen.get_windows()
        for w in win_list:
            ws_workspace = w.get_workspace()
            if is_urgent(w):
                # Urgent windows are always noted.
                self.workspace_states[ws_workspace] |= PagerModel.URGENT
            elif is_skipped(w):
                # We ignore these for obvious reasons.
                continue
            else:
                # Minimised.
                if is_mini(w):
                    self.workspace_states[ws_workspace] |= PagerModel.MINIMISED
                # Just a normal window.
                else:
                    self.workspace_states[ws_workspace] |= PagerModel.OCCUPIED

        # Set the active workspace.
        a = self.screen.get_active_workspace()
        for i in self.workspaces:
            if i is a:
                self.workspace_states[i] |= PagerModel.ACTIVE
                break

    def change_workspace(self, screen, prev):
        # Disable the 'active' flag on the old workspace.
        self.workspace_states[prev] &= ~PagerModel.ACTIVE

        # And enable it on the now-current one.
        cur = self.screen.get_active_workspace()
        self.workspace_states[cur] |= PagerModel.ACTIVE

    def get_state(self, ws):
        """ Get the state bitmask for a workspace. """
        if isinstance(ws, int):
            return self.workspace_states[self.workspaces[ws]]
        elif isinstance(ws, str):
            for i in self.workspaces:
                if i.get_name() == ws:
                    return self.workspace_states[i]
            return None # Couldn't find it :/
        else:
            return self.workspace_states[ws]

    def get_state_list(self):
        return [self.workspace_states[i] for i in self.workspaces]
        
    def is_active(self, ws):
        state = self.get_state(ws)
        return state & PagerModel.ACTIVE

    def get_workspace_number(self, num):
        return self.workspaces[num]
