from gi.repository import Clutter, GObject
import arrow

class ClockApplet(Clutter.Text):
    def __init__(self, conf):
        Clutter.Text.__init__(self)

        self.set_font_name(conf.getfont("Clock"))
        self.set_text("[Clock]")
        self.set_color(conf.getcolour("Clock", "font-colour"))
        
        self.format = conf.get("Clock", "format")
        self.refresh()

    def refresh(self, *args):
        self.set_text(arrow.now().format(self.format))
        self.timer_id = GObject.timeout_add_seconds(1, self.refresh, None)
        self.queue_redraw()
