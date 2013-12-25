# cult-panel

The Crappy Useless Little Toy-panel.

======

##Building:

cult-panel is written in pure Python 3. It makes use of the Python standard library, and the [Arrow](https://github.com/crsmithdev/arrow) library for time formatting.

It does, require GObject introspection, and the following C libraries:
 - `libwnck`
 - `gtk`, `gdk`, `gdkx11`, `gobject`
 - `clutter`, `gtkclutter`

Also, `scons` is used for installation.

##Installing:

Simply run `scons install`.

To specify a prefix, use `scons install prefix=/MY/COOL/PREFIX/`; the default is /usr/local/

##Running:

`cult-panel` does not (at the moment) support any command line flags. All options are set in the config file (or hard coded).

A panel is spawned for each file found in ~/.config/cult-panel/ which ends in .cfg. They should be in Python's ConfigParser format (i.e. INI-like).

A default/example config file is installed to $PREFIX/share/cult-panel.cfg.default. The ultimate reference is, of course, the code, and all (important) options are detailed in `Config.py`.
