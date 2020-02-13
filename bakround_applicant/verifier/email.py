__author__ = "natesymer"

"""
Implements a means of connecting to an email address via IMAP
and reading messages. Usage with gmail requires you to both:
1. Enable IMAP
2. Enable insecure apps

Example (using Gmail):

inbox = Mailbox(username="<some email>",
                password="<some password>",
                host="imap.gmail.com",
                port=993)

for email_message in inbox.messages():
    print(email_message.from_email)

"""

import imaplib
import email
import time
import datetime

from django.utils.timezone import make_aware

from bakround_applicant.utilities.logger import LoggerFactory

class IMAPError(Exception):
    def __init__(self, status_code, phase):
        super().__init__("Encountered IMAP status code {} ({}).".format(status_code, phase))
        self.status_code = status_code
        self.phase = phase

class Mailbox:
    def __init__(self, username=None, password=None, host=None, port=None):
        self.username = username
        self.password = password
        self.mail = imaplib.IMAP4_SSL(host=host, port=port)
        self.logger = LoggerFactory.create("MAILBOX ({})".format(self.username))

    def authenticate(self):
        try:
            self.mail.login(self.username, self.password)
            return True
        except Exception as e:
            print(str(e))
            return False

    def messages(self, mailbox = 'inbox', from_email=None, since=None, header=None):
        query = []

        if from_email:
            query.append("FROM {}".format(from_email))

        if since:
            query.append("SENTSINCE {}".format(since.strftime("%d-%b-%Y")))

        if header:
            header_name, value = header
            query.append("{} \"{}\"".format(header_name, value))

        query = "{}".format(' '.join(query))

        self.logger.info("Querying mailbox `{}` with query `{}`".format(mailbox, query))

        self.mail.select(mailbox)
        result, data = self.mail.uid('search', None, query)

        if result != 'OK':
            raise IMAPError(status_code=result, phase='search {}'.format(query))

        uids = list(data[0].decode('utf-8').split(' '))
        uids.reverse()

        self.logger.info("Found {} email messages.".format(len(uids)))

        for uid in uids:
            result, data = self.mail.uid('fetch', uid, '(RFC822)')
            if result != "OK":
                raise IMAPError(status_code=result, phase="fetch {}".format(uid))
            yield EmailMessage(rfc822_data=data)

class EmailMessage:
    def __init__(self, rfc822_data=None):
        self.raw_email = rfc822_data[0][1]
        self.parsed_email = email.message_from_string(self.raw_email.decode('utf-8'))

    @property
    def to_email(self):
        return email.utils.parseaddr(self.parsed_email['To'])[-1] or None

    @property
    def from_email(self):
        return email.utils.parseaddr(self.parsed_email['From'])[-1] or None

    @property
    def subject(self):
        return self.parsed_email["Subject"] or None

    @property
    def received(self):
        date_tz = self.parsed_email['Received'].split('\n')[-1]
        parsed = email.utils.parsedate_tz(date_tz)[:-1]
        return make_aware(datetime.datetime.fromtimestamp(time.mktime(parsed)))

    @property
    def indeed_metadata(self):
        return {
            "fbl": self.parsed_email.get('X-Indeed-FBL'),
            "client_app": self.parsed_email.get('X-Indeed-Client-App'),
            "content_type": self.parsed_email.get('X-Indeed-Content-Type'),
            "tk": self.parsed_email.get('X-Indeed-TK')
        }

    @property
    def text(self):
        maintype = self.parsed_email.get_content_maintype()
        if maintype == 'multipart':
            for part in self.parsed_email.get_payload():
                if part.get_content_maintype() == 'text':
                    return part.get_payload()
        elif maintype == 'text':
            return self.parsed_email.get_payload()

