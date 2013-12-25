#!/usr/bin/env python3.3

import os, os.path, sys

# This has to come before the Clutter/Gtk/Wnck imports.
from gi.repository import GtkClutter, Gtk
GtkClutter.init(sys.argv)

# Expose these modules if we need to.
import Panel, PagerModel
import Taskbar, Clock, Pager, Battery

from Config import cultConfig

try:
    from xdg import BaseDirectory
    CONF_DIR = os.path.join(BaseDirectory.xdg_config_home, "cult-panel")
except ImportError as e:
    CONF_DIR = os.path.join(os.environ["HOME"],".config", "cult-panel")

print(CONF_DIR)

if __name__ == "__main__":
    # Find all the config files in the config directory, and spawn a panel for each of them.
    panels = []
    confs = [os.path.join(CONF_DIR, k)
             for k in os.listdir(CONF_DIR)
             if k[-4:] == ".cfg"]

    for cfg_file in confs:
        print("loading panel config " + cfg_file + "...")
        conf = cultConfig(cfg_file)
        panels.append(Panel.Panel(conf))

    for p in panels:
        p.setup_visuals()

    if panels:
        Gtk.main()
