__author__ = "natesymer"

from types import GeneratorType

from .browser_action import BrowserAction
from .exceptions import BrowserActionNonFatalError, BrowserActionFatalError
from .browser import Browser, BrowserFatalError, BrowserRecoverableError
from .browser_pool import BrowserPool

class BrowserActionState:
    def __init__(self, browser_pool = None):
        self.pool = browser_pool or BrowserPool()
        self.requires_tor = False
        self.in_contiguous = False
        self.contiguous_browser = None
        self.result = None
        self.context = {}

    def require_tor(self, on):
        """Set whether or not the BrowserActionState will require the browsers it uses to use Tor."""

        # We can't change whether a browser will use tor while contiguous
        if self.in_contiguous and self.contiguous_browser:
            raise BrowserActionFatalError("Already in contiguous. This is a coding error.")
        self.requires_tor = on
        return self

    def begin_contiguous(self):
        if self.in_contiguous:
            raise BrowserActionFatalError("Already in contiguous. This is a coding error.")
        self.in_contiguous = True
        return self

    def end_contiguous(self):
        self.in_contiguous = False
        if self.contiguous_browser:
            self.pool.release(self.contiguous_browser[0],
                              self.contiguous_browser[1])
            self.contiguous_browser = None
        return self

    def for_each(self, key, action_cls, **kwargs):
        lst = self.result
        if not (isinstance(lst, list) or isinstance(lst, GeneratorType)):
            lst = [lst]

        for x in lst:
            self.do(action_cls, **({**kwargs, key: x }))

        return self

    def _get_browser(self):
        return self.pool.get(use_tor=self.requires_tor)

    def do(self, action_cls, **kwargs):
        errors = []
        while True:
            try:
                b = None
                if self.in_contiguous and not self.contiguous_browser:
                    self.contiguous_browser = self._get_browser()

                b = self.contiguous_browser if self.in_contiguous else self._get_browser()
                b[0].resets_ip = self.requires_tor
                b[0].cookies_enabled = not self.requires_tor

                if not b[0].cookies_enabled:
                    del b[0].cookies

                action = action_cls(**kwargs)
                action._set_context(self.context)
                self.result = action.go(b[0])
                self.context = action._get_context()
                break
            except (BrowserActionNonFatalError, BrowserRecoverableError) as e:
                b[1] = 0 # let's just kill the browser by setting its remaining uses to 0.
                b[0].close()
                errors.append(e)
                if len(errors) > 5:
                    e_fatal = BrowserActionFatalError("Encountered too many non-fatal errors.")
                    action.on_fatal_error(e_fatal)
                    raise e_fatal
                    break
                else:
                    action.on_nonfatal_error(e)
            finally:
                if not self.in_contiguous and b and len(b) > 1:
                    self.pool.release(b[0], b[1] - 1)

        return self
