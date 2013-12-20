#!/usr/bin/env python3

# Expose these modules if we need to.
import Panel, PagerModel
import Taskbar, Clock, Pager, Battery

if __name__ == "__main__":
    # Eventually, handle multiple panels running from different config files.
    # For now, just spawn the one of them.
    panel = Panel.Panel()
    panel.run()
