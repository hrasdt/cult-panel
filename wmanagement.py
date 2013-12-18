from gi.repository import Clutter, Wnck, Gdk

class Workspace (object):
    NO_WINDOWS = ""
    MINIMISED  = "m" # Minimised window.
    OCCUPIED   = "o" # A normal window.
    URGENT     = "u" # Window requesting attention.
    ACTIVE     = "a" # The active workspace.

    def __init__(self, workspace, windows = []):
        self.wnck_ws = workspace
        self.number = workspace.get_number()
        self.name = workspace.get_name()

        # A list of all windows.
        self.windows = windows

        # Count of windows in various states.
        self.minimised = []
        self.normal = []
        self.urgent = []

        # Is this the active workspace?
        self.active = False

        self.state = ""
        self.update_state()
        
    def update_state(self):
        self.state = Workspace.NO_WINDOWS
        
        self.name = self.wnck_ws.get_name()
        self.number = self.wnck_ws.get_number()
        
        # Find the most important state.
        for win in self.windows:
            ws = win.get_workspace()
            if ws != self.wnck_ws:
                # Something's screwy.
                if ws in self.windows:
                    self.windows.remove(ws)
                continue
            
            if win.needs_attention():
                self.state += Workspace.URGENT
            elif not is_skipped(win) and not win.is_minimized():
                self.state += Workspace.OCCUPIED
            elif not is_skipped(win) and win.is_minimized():
                self.state += Workspace.MINIMISED

        self.state += Workspace.ACTIVE if self.active else ""
        return self.state

    def add_window(self, win):
        if win in self.windows: return

        self.windows.append(win)

        if win.needs_attention():
            self.urgent.append(win)
            self.state += Workspace.URGENT
        elif is_skipped(win): return
        
        else:
            if win.is_minimized():
                self.minimised.append(win)
                self.state += Workspace.MINIMISED
            else:
                self.normal.append(win)
                self.state += Workspace.OCCUPIED

    def remove_window(self, win):  
        if win in self.windows:
            self.windows.remove(win)
        else:
            return
            
        l = list(self.state)
        if win in self.minimised:
            self.minimised.remove(win)
            l.remove(Workspace.MINIMISED)
            self.state = "".join(l)
            
        elif win in self.normal:
            self.normal.remove(win)
            l.remove(Workspace.OCCUPIED)
            self.state = "".join(l)

        elif win in self.urgent:
            self.urgent.remove(win)
            l.remove(Workspace.URGENT)
            self.state = "".join(l)

    def set_active(self, val = True):
        self.active = val
        if not val:
            self.state = self.state.replace(Workspace.ACTIVE, "")
        else:
            self.state += Workspace.ACTIVE

    def get_state(self):
        return self.state

def is_skipped(win):
    return win.is_skip_tasklist() or win.is_skip_pager()

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

def get_used_workspaces():
    """ Get a list of active workspaces.

    This returns a string representing the state of all windows.
    Symbols are defined in Pager.
    
    Windows for which skip-tasklist/pager are set will not be counted, unless they're also marked "urgent".
    """
    screen = Wnck.Screen.get_default()
    
    windows = screen.get_windows()
    workspaces = screen.get_workspaces()

    workspace_d = {key: Workspace(key) for key in workspaces}
    for win in windows:
        ws = win.get_workspace()
        if ws is None:
            # This happens for sticky windows.
            continue
        else:
            workspace_d[ws].windows.append(win)

    # Set the active workspace.
    workspace_d[screen.get_active_workspace()].active = True

    # Build the (in-order) list of workspaces.
    workspace_list = list(workspace_d.values())
    workspace_list.sort(key = lambda i: i.number)

    for w in workspace_list:
        w.update_state()
    
    return workspace_list
