__author__ = "natesymer"

from ... import BrowserAction

class CrawlResumes(BrowserAction):
    # BrowserAction
    scraper_job = None

    # CONSTANTS
    link_selector = ".rezemp-ResumeSearchCard a.icl-TextLink--primary"

    def get_start_url(self):
        self.scraper_job.refresh_from_db()
        start_url = self.scraper_job.start_url
        if self.scraper_job.start_offset:
            if "?" in start_url:
                start_url += "&"
            else:
                start_url += "?"

            start_url += "start={}".format(str(self.scraper_job.start_offset))
        return start_url

    def finish_crawling(self):
        self.scraper_job.refresh_from_db()
        self.scraper_job.running = False
        self.scraper_job.save()

    def get_href(self, el):
        return el.get_attribute('href')

    def go(self, browser):
        while True:
            print("Starting process-------Getting Indeed resumes")
            start_url = self.get_start_url()
            self.logger.info("Crawling {} ({} cookies)".format(start_url, "with" if browser.cookies else "without"))
            browser.href = start_url

            # Scrape the hrefs out of the page upfront to avoid selenium "Element Detached" errors.
            results = list(filter(bool, map(self.get_href, browser.selector(self.link_selector, wait = 60, many = True, nothrow = True) or [])))
            if not results:
                self.logger.info("No {}resumes found.".format("more " if self.scraper_job.start_offset > 0 else ""))
                self.finish_crawling()
                break

            for href in results:
                slug = href.strip().split("?")[0].rstrip('/').split('/')[-1]
                if slug:
                    self.logger.info("Found Indeed resume slug: {}".format(slug))
                    yield "https://www.indeed.com/r/" + slug
                    self.scraper_job.refresh_from_db()
                    self.scraper_job.start_offset += 1
                    self.scraper_job.save()
