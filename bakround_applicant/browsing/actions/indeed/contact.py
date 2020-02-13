__author__ = "natesymer"

from ... import BrowserAction

class IndeedMessage:
    recruiter_name = None
    company_name = None
    message = None
    job_title = None
    job_description = None

class ContactOnIndeed(BrowserAction):
    url = None # URL of resume belonging to profile to contact.
    message = None # An IndeedMessage

    def go(self, browser):
        browser.href = self.url

        # First, we check to see if we've already contacted the candidate through Indeed.

        by_user = browser.selector(".rezemp-ContactedLabel-byUser", wait=10, nothrow=True)
        by_coworker = browser.selector(".rezemp-ContactedLabel-byCoworker", wait=10, nothrow=True)

        if by_user and by_user.get_attribute("textContent"):
            self.logger.info("Already contacted at {}.".format(self.url))
            return False
        
        if by_coworker and by_coworker.get_attribute("textContent"):
            self.logger.info("Already contacted at {} by an 'Indeed Coworker'.".format(self.url))
            return False

        # If we haven't already contacted them, automate the contact

        recruiter_name = browser.selector("input#input-senderName", wait=10, required=True)
        recruiter_name.clear()
        recruiter_name.send_keys(self.message.recruiter_name)

        company_name = browser.selector("input#input-senderCompany", wait=10, required=True)
        company_name.clear()
        company_name.send_keys(self.message.company_name)

        message = browser.selector("textarea#textarea-message", wait=10, required=True)
        message.clear()
        message.send_keys(self.message.message)

        job_title = browser.selector("input#input-jobTitle", wait=10, required=True)
        job_title.clear()
        job_title.send_keys(self.message.job_title)

        job_description = browser.selector("textarea#textarea-jobDescription", wait=10, required=True)
        job_description.clear()
        job_description.send_keys(self.message.job_description)

        self.logger.info("Filled out form at {}".format(self.url))

        submit = browser.selector("button.rezemp-submitContact", wait=10, required=True)
        browser.scroll_to(submit)
        submit.click()

        self.logger.info("Clicked submit at {}".format(self.url))
        
        return True
