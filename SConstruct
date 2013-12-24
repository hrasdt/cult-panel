import os

env = Environment()
lib_name = "cult-panel"

module_objs = [
    "Battery.py",
    "Taskbar.py",
    "Clock.py",
    "Pager.py",
    "PagerModel.py",
    "Panel.py",
    "WmInteraction.py",
    "Config.py",
    "main.py",
    "__init__.py", # Why we might want this, I don't know.
    ]

prefix = ARGUMENTS.get("prefix", "/usr/local/")

Alias("install-bin",
      Install(os.path.join(prefix, "bin"),
              ["cult-panel"]))
Alias("install-lib",
      Install(os.path.join(prefix, "lib", lib_name),
              module_objs))
Alias("install-share",
      Install(os.path.join(prefix, "share"),
              ["cult-panel.cfg.default"]))

Alias("install",
      ["install-lib", "install-bin", "install-share"])

Alias("uninstall",
      env.Command("uninstall", None, Delete(FindInstalledFiles())))
