__author__ = "natesymer"

from .browser import Browser

class BrowserPool:
    def __init__(self, uses_per_browser=5):
        self.browsers = []
        self.uses_per_browser = uses_per_browser

    def get(self, use_tor=False):
        """Get a browser from the pool."""
        browser = None
        for (b, uses) in self.browsers:
            if (use_tor and b.uses_tor) or not use_tor:
                browser = (b, uses)
                b.reset()
                break

        if not browser:
            browser = (Browser(uses_tor=use_tor), self.uses_per_browser)

        return browser

    def release(self, browser, uses):
        """Return a browser to the pool. Set the number of uses left. 0 or
           fewer uses results in the browser being terminated."""
        if uses <= 0:
            browser.close()
        else:
            self.browsers.append((browser, uses))
  
    def drain(self):
        """Close all browsers and empty the pool."""
        for b in self.browsers:
            b[0].close()

        self.browsers = []

    def __del__(self):
        self.drain()

