
from gi.repository import Clutter
import sys

class cultStyle(object):
    def __init__(self, path):
        # Parse the theme lines.
        self.colours = {}
        self.fontfam = "Sans"
        self.fontsize = 12
        self.clock_format = "HH:mm:ss - DD.MM.YY"
        
        with open(path, "r") as ff:
            for line in ff.readlines():
                args = line.split()
                if len(args) < 1\
                  or args[0][0] in (";", "#")\
                  or args[0][0:3] == "//":
                    continue

                # Colours are stored in a hashtable.
                elif args[0] in ("col", "colour", "color"):
                    item, colour = args[1:]
                    self.colours[item] = colour

                # Fonts.
                elif args[0] == "font-family":
                    self.fontfam = args[1]
                elif args[0] == "font-size":
                    self.fontsize = args[1]


                # Clock formatting.
                elif args[0] == "clock":
                    self.clock_format = " ".join(args[1:])

    def get_hex(self, obj):
        return self.colours[obj]

    def get_scalar(self, obj):
        if not obj + "-scalar" in self.colours:
            self.colours[obj + "-scalar"] = self.hex_to_scalar(self.colours[obj])
            
        return self.colours[obj + "-scalar"]
        
    def hex_to_scalar(self, col):
        """ Normalised colours are stored as a tuple of 3 elements in [0.0, 1.0]."""
        if col[0] == "#" and len(col) == 7:
            return tuple(map(lambda x: int(x, 16) / 256.0,
                             [col[1:3], col[3:5], col[5:7]]))
        elif col[0] == "#" and len(col) == 4:
            return tuple(map(lambda x: int(x, 16) / 16.0,
                             [col[1:2], col[2:3], col[3:4]]))

def load_style(path):
    """ Load a style from disk, returning the cultStyle object holding it. """
    return cultStyle(path)
