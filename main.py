#!/usr/bin/env python3

import os

# Expose these modules if we need to.
import Panel, PagerModel
import Taskbar, Clock, Pager, Battery

from Config import cultConfig

if __name__ == "__main__":
    # Eventually, handle multiple panels running from different config files.
    # For now, just spawn the one of them.
    conf = cultConfig(os.environ["XDG_CONFIG_HOME"] + "/cult-panel/default.cfg")
    
    panel = Panel.Panel(conf)
    panel.run()
