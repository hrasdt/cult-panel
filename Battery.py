from gi.repository import Clutter, GObject
import arrow

def read_file(fpath):
    data = ""
    with open(fpath, 'r') as ff:
        data = ff.read()
    return data

class BatteryApplet (Clutter.Text):
    def __init__(self, path = "/sys/class/power_supply/BAT0/",
                 fmt = "{state} - {capacity}%",
                 font_desc = "Bauhaus 9",
                 colour = None):
        Clutter.Text.__init__(self)

        # The label format.
        self.format = fmt

        # Where we query.
        self.path = path

        # Theme.
        self.set_font_name(font_desc)
        if colour:
            self.set_color(colour)

        self.refresh()

    def refresh(self, *ignored):
        """ Update the battery state. """
        capacity_ = int(read_file(self.path + "capacity"))
        state_ = read_file(self.path + "status").strip()

        text = self.format.format(capacity = capacity_,
                                  state = state_)
        self.set_text(text)
        self.timer_id = GObject.timeout_add_seconds(30, self.refresh, None)
        self.queue_redraw()
