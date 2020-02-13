__author__ = "natesymer"

from .exceptions import BrowserActionNonFatalError, BrowserActionFatalError
from bakround_applicant.utilities.logger import LoggerFactory

class BrowserAction:
    """Abstract class for controlling a headless browser."""
    def __init__(self, *args, **kwargs):
        self.logger = LoggerFactory.create(type(self).__name__)
        for k, v in kwargs.items():
            setattr(self, k, v)

    def _set_context(self, ctx):
        self.__context = ctx

    def _get_context(self):
        return self.__context

    def __getitem__(self, key):
        return self.__context.get(key)

    def __setitem__(self, key, value):
        self.logger.debug("Setting context[{}] = {}".format(key, value))
        self.__context[key] = value
        return self.__context[key] # keep semantics consistent with developer expectations

    def restart(self, message = None):
        self.logger.debug("Restarting: {}".format(message))
        raise BrowserActionNonFatalError(message)

    def fail(self, message = None):
        self.logger.debug("Failing: {}".format(message))
        raise BrowserActionFatalError(message)

    def on_nonfatal_error(self, error):
        """OVERRIDE ME: Called when a nonfatal error is encountered. The BrowserAction
           will be evaluated again (the error is swallowed); use this method to reset any state."""
        pass

    def on_fatal_error(self, error):
        """OVERRIDE ME: Called when a fatal error is encountered. The BrowserAction won't be evaluated again.K"""
        pass

    def go(self, browser):
        """OVERRIDE ME: Use `browser` to do some action. `yield` stuff. Return stuff. Call `self.{fail,restart}()`."""
        raise NotImplemented

