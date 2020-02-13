__author__ = "natesymer"

# These are BrowserAction-Level errors. They indicate that
# something has gone wrong on a much higher level than a
# hardware failure, network failure, (n / 0), etc...
#
# These are logical errors. They indicate that conditions
# in browsing were insane.

# When this error is thrown by a BrowserAction,
# the browser action is re-tried.
class BrowserActionNonFatalError(Exception):
    pass

# When this error is thrown by a BrowserAction,
# the browser action is terminated and browsing STOPS.
# THIS ERROR IS NOT SWALLOWED. EVER.
class BrowserActionFatalError(Exception):
    pass

