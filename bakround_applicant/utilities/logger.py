import logging
import socket
from logging.handlers import SysLogHandler
import traceback


def format_traceback(exc_info, app_name):
    s = "\n".join(traceback.format_exception(*exc_info)).replace("\n\n", "\n")
    return app_name + " " + s.replace("\n", "\n" + app_name + " ")


class LoggerFactory(object):

    @staticmethod
    def create(app_name):

        class ContextFilter(logging.Filter):

            #hostname = host_name
            hostname = 'services.bakround.com' #socket.gethostname()

            def filter(self, record):
                record.hostname = ContextFilter.hostname
                return True

        logger = logging.Logger(app_name)
        logger.setLevel(logging.INFO)

        f = ContextFilter()
        logger.addFilter(f)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(app_name + " %(message)s")
        formatter.formatException = (lambda exc_info: format_traceback(exc_info, app_name))
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger
