__author__ = "natesymer"

from ..login import LoginAction

class IndeedLogin(LoginAction):
    def cred_pred(self, scraper_login):
        return scraper_login.source in ['indeed']

    def login(self, browser, scraper_login):
        browser.href = 'https://secure.indeed.com/account/login'
        browser.selector("#loginform input[type=email]",
                         wait = 5,
                         visible = True,
                         required = True).send_keys(scraper_login.user_name)
        browser.selector("#loginform input[type=password]",
                         wait = 5,
                         visible = True,
                         required = True).send_keys(scraper_login.password)
        browser.selector("#loginform button[type=submit]", wait = 5, visible = True, required = True).click()

