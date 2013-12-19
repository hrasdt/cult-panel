from gi.repository import Clutter, Wnck
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
def get_pager_model():
    """ Get a representation of the active workspaces.

    Windows for which skip-pager are set will not be counted, unless they're also marked "urgent".
    """
    global _g_model

    if _g_model is None:
        _g_model = PagerModel()

    return _g_model

def get_pager_state(ws):
    return get_pager_model().get_state(ws)

def update_pager_state(window, change_mask, new_state):
    ws = window.get_workspace()
    get_pager_model().recalculate_workspace_state(ws)

def workspace_by_number(num):
    return get_pager_model().get_workspace_number(num)

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
        self.workspace_states[a] |= PagerModel.ACTIVE

    def change_workspace(self, screen, prev):
        # Disable the 'active' flag on the old workspace.
        self.workspace_states[prev] &= ~PagerModel.ACTIVE

        # And enable it on the now-current one.
        cur = self.screen.get_active_workspace()
        self.workspace_states[cur] |= PagerModel.ACTIVE

    def window_workspace_changed(self, win):
        ws = win.get_workspace()

        # Remove it from whereever it was before now.
        for w in [None] + self.workspaces:
            self.tasklist[w] = [K for K in self.tasklist[w] if K is not win]

        if ws is not None:
            self.tasklist[ws].append(win)
        self.recalculate_workspace_state(ws)

    def add_window(self, screen, win):
        workspace = win.get_workspace()
        
        # Update the tasklist.
        if not is_skipped_tasklist(win):
            self.tasklist[workspace].append(win)
            # Connect the signals.
            win.connect("workspace-changed", self.window_workspace_changed)
            win.connect("state-changed", update_pager_state)
            
        self.recalculate_workspace_state(workspace)
    
    def remove_window(self, screen, win):
        """ Remove a window from the pager (e.g. if it's closed). """
        ws = win.get_workspace()
        if win in self.tasklist[ws]:
            self.tasklist[ws].remove(win)

        if ws is not None:
            self.recalculate_workspace_state(ws)

    def recalculate_workspace_state(self, workspace = -1):
        if isinstance(workspace, int) and workspace == -1:
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
                        return
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
