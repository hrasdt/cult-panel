from gi.repository import Clutter, GObject
import arrow

class ClockApplet(Clutter.Text):
    def __init__(self, timefmt,
                 font_desc = "Bauhaus 9",
                 colour = None):
        
        Clutter.Text.__init__(self)

        self.set_font_name(font_desc)
        self.set_text("[Clock]")
        if colour:
            self.set_color(colour)
        
        self.format = timefmt
        self.refresh()

    def refresh(self, *args):
        self.set_text(arrow.now().format(self.format))
        self.timer_id = GObject.timeout_add_seconds(1, self.refresh, None)
        self.queue_redraw()
