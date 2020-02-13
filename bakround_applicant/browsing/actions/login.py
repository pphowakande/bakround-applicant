__author__ = "natesymer"

from .. import BrowserAction, BrowserActionFatalError, BrowserActionNonFatalError, BrowserRecoverableError, BrowserFatalError
from ...scraping.models import ScraperLogin
from bakround_applicant.utilities.logger import LoggerFactory

class LoginAction(BrowserAction):
    credential = None
    credentials = None

    def login(self, browser, scraper_login):
        """OVERRIDE ME: perform the browser actions required to actually log in"""
        pass

    def cred_pred(self, scraper_login):
        """OVERRIDE ME: test if a ScraperLogin is suitable for scraping."""
        return True

    def next_credential(self):
        """Cycles through credentials a scraper could theoretically use to log in. Infinite."""
        while True:
            recreated = False
            if not self.credentials:
                recreated = True
                self.credentials = ScraperLogin.objects.filter(enabled=True).order_by('adjusted_failure_count').iterator()
            
            try:
                while True:
                    v = self.credentials.__next__()
                    if v and self.cred_pred(v):
                        return v
            except StopIteration:
                self.credentials = None
                if recreated: # None of the logins work, because we just fetched them all!
                    raise BrowserActionFatalError("No suitable credentials for login.")

    def attempt_login(self, browser, credential, singular=False):
        self.logger.debug("Preparing browser for authentication")
        del browser.cookies
        browser.cookies_enabled = True
        try:
            self.login(browser, credential)
            self.logger.info("Successfully authenticated using {} id {}".format(type(credential).__name__, credential.id))
            self['current_credential'] = credential
            return True
        except (BrowserActionNonFatalError, BrowserRecoverableError):
            self.logger.info("Failed to login using {} id {}".format(type(credential).__name__), credential.id)
            browser.reset()
            if singular:
                raise
        return False

    def go(self, browser):
        if browser.uses_tor:
            raise BrowserActionFatalError("Authenticating in a Tor browser is anathema.")

        if self.credential:
            self.attempt_login(browser, self.credential, singular=True)
        else:
            while True:
                if self.attempt_login(browser, self.next_credential()):
                    break

def with_failure_rate(decor_arg):
    class ClassWrapper(decor_arg):
        def go(self, browser):
            try:
                super().go(browser)
                if self['current_credential']:
                    self['current_credential'].refresh_from_db()
                    self['current_credential'].adjusted_failure_count -= 1
                    if self['current_credential'].adjusted_failure_count < 0:
                        self['current_credential'].adjusted_failure_count = 0
                    self['current_credential'].save()
            except (BrowserActionNonFatalError, BrowserRecoverableError):
                if self['current_credential']:
                    self['current_credential'].refresh_from_db()
                    self['current_credential'].adjusted_failure_count += 1
                    self['current_credential'].save()
                raise
            except (BrowserActionFatalError, BrowserFatalError):
                if self['current_credential']:
                    self['current_credential'].refresh_from_db()
                    self['current_credential'].adjusted_failure_count += 5
                    self['current_credential'].save()
                raise

    ClassWrapper.__name__ = "{}WithFailureRate".format(decor_arg.__name__)

    return ClassWrapper

