from subprocess import call

def window_manager_menu():
    # For the moment, assume that we're using fluxbox.
    call(["fluxbox-remote", "RootMenu"])

def set_xprop_struts(window_id,
                     left, right, top, bottom):
    strut = '"{l}, {r}, {t}, {b}"'.format(l=left, r=right,
                                          t=top, b=bottom)
    call(["xprop",
          # Set the format.
          "-f", "_NET_WM_STRUT", "32c",
          # Get the right window.
          "-id", str(window_id),
          # Set the STRUT property.
          "-set", "_NET_WM_STRUT", strut])

