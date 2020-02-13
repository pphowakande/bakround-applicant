__author__ = "natesymer"

from . import *
from .actions.login import with_failure_rate
from .actions.indeed.crawl_resumes import CrawlResumes
from .actions.icims.crawl_icims import CrawlIcims
from .actions.indeed.scrape_resume import ScrapeIndeedResume
from .actions.icims.scrape_resume import ScrapeIcimsData
from .actions.indeed.login import IndeedLogin
from .actions.indeed.contact import ContactOnIndeed
from bakround_applicant.all_models.db import ProfileResume

def icims_spider(ranking_job, on_resume):
    return (BrowserActionState()
             .require_tor(True)
             .do(CrawlIcims, ranking_job=ranking_job)
             .for_each("url", ScrapeIcimsData, on_resume=on_resume))

def indeed_spider(scraper_job, on_resume):
    return (BrowserActionState()
             .require_tor(True)
             .do(CrawlResumes, scraper_job=scraper_job)
             .for_each("url", ScrapeIndeedResume, on_resume=on_resume))

def indeed_re_scrape(profile_resume, on_resume):
    return (BrowserActionState()
             .begin_contiguous()
             .do(IndeedLogin)
             .do(with_failure_rate(ScrapeIndeedResume), url=profile_resume.url, on_resume=on_resume)
             .end_contiguous())

def indeed_external_contact(profile, message, scraper_login):
    profile_resume = ProfileResume.objects.filter(profile_id=profile.id).order_by("-date_created").first()
    if not profile_resume:
        raise ValueError("Missing ProfileResume!")

    if not profile_resume.url:
        raise ValueError("ProfileResume id {} is missing a url.".format(profile_resume.id))

    return (BrowserActionState()
             .begin_contiguous()
             .do(IndeedLogin, credential=scraper_login)
             .do(with_failure_rate(ContactOnIndeed), url=profile_resume.url, message=message)
             .end_contiguous())
