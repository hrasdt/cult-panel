from gi.repository import Clutter, Wnck

# For time mangling.
import arrow

# From Python's standard library.
# It'd be nice to write my own Fluxbox-style tree config which accepts globs,
# but for the moment, any configuration is better than none.
import configparser

from Panel import Panel

DEFAULTS = {
    "DEFAULT": {"font-name":	"Sans",
                "font-size":	9,
                "font-colour": "#000000",
                },
    "Panel": {"size": 16,
              "orientation": "top",
              "order": "t|p|bc",
              "background": "#ffffff", # idk lol
              "screen": 0, # The screen on which we are displaying. Untested.
              },

    "Pager": {"enable": True,
              "size": 8,

              "active": "#ffffff",
              
              "occupied": "#aaaaaa",
              "minimised": "#707070",
              "urgent": "#ffffff",
              "none": "#404040",
              },

    "Taskbar": {"enable": True,
                "all-workspaces": False,
                "show-icons": True,
                "show-labels": True,

                "active": "#404040",
                "normal": "#303030",
                "minimised": "#0f0f0f",
                "urgent": "#505050",

                "fixed-width": False,
                "height": "{Panel:size}",
                "width": 140,
                },
              
    "Clock": {"enable": True,
              "format": "HH:mm - DD.MM.YY",
              },

    "Battery": {"enable": True,
                "path": "/sys/class/power_supply/BAT0/",
                "format": "{state} - {capacity}%",
                },
    }

class cultConfig(configparser.ConfigParser):
    def __init__(self, path):
        configparser.ConfigParser.__init__(self,
                                           interpolation = configparser.ExtendedInterpolation())

        self.read_dict(DEFAULTS.copy())
        self.read(path)

    def getcolour(self, section, name):
        return Clutter.Color.from_string(self.get(section, name))[1]

    def getfont(self, section):
        return self.get(section, "font-name")\
           + " " + self.get(section, "font-size")

    def getscreen(self):
        return Wnck.Screen.get(self.getint("Panel", "screen"))
           
    def is_vertical(self):
        return self.get("Panel", "orientation") in ["left", "right"]
