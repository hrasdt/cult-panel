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
    "main.py",
    "__init__.py", # Why we might want this, I don't know.
    ]

prefix = ARGUMENTS.get("prefix", "/usr/local/")
print(prefix)

Alias("install-bin",
      Install(os.path.join(prefix, "bin"),
              ["cult-panel"]))
Alias("install-lib",
      Install(os.path.join(prefix, "lib", lib_name),
              module_objs))

Alias("install",
      ["install-lib", "install-bin"])

Alias("uninstall",
      env.Command("uninstall", None, Delete(FindInstalledFiles())))
