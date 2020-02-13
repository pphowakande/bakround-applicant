__author__ = "natesymer"

import os
import time
from bakround_applicant.services.queue import QueueConnection
import psycopg2
from django.core.management import call_command

try:
    from django.core.servers.basehttp import get_internal_wsgi_application as WSGIHandler
except ImportError:
    from django.core.handlers.wsgi import WSGIHandler

def configure_django(migrate=False, rabbitmq=False, postgres=False, default_local=False):
    # Make sure our environment is sane.
    sanitize_environment(default_local)

    # Load the Django ORM
    import django
    django.setup()

    perform_checks()

    if postgres or migrate:
        wait_postgres()

    # RabbitMQ can take a long time to start up.
    # in the mean time, we can migrate.
    if migrate:
        initialize_db()

    if rabbitmq:
        wait_rabbitmq()

def clear_caches():
    try:    call_command("invalidate_cachalot")
    except: pass

def collect_static():
    # os.system("mkdir staticfiles || true")
    try: os.mkdir("./staticfiles")
    except: pass

    call_command("collectstatic", interactive=False)

def is_local_env():
    settings_module = os.environ.get("DJANGO_SETTINGS_MODULE")
    return settings_module == "bakround_applicant.settings.local"

def sanitize_environment(default_local = False):
    default_settings = "bakround_applicant.settings.{}".format("local" if default_local else "production") 
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", default_settings)
    if not os.environ.get("DJANGO_SETTINGS_MODULE"):
        os.putenv("DJANGO_SETTINGS_MODULE", default_settings)        
        os.environ["DJANGO_SETTINGS_MODULE"] = default_settings

    # Nota Bene: The rest of the POSTGRES_* env vars shouldn't require modification

    db_port = os.environ.get("POSTGRES_PORT") or str(5432)
    os.putenv('POSTGRES_PORT', db_port)
    os.environ["POSTGRES_PORT"] = db_port

def wait_postgres():
    # If we're running locally, we use a Docker container to mock
    # out our RDS Postgres instance. If we're in prod, said DB server
    # will already be running and there is no need to wait.
    if is_local_env():
        db_host = os.environ.get("POSTGRES_HOST")
        db_name = os.environ.get("POSTGRES_DB")
        db_user = os.environ.get("POSTGRES_USER")
        db_password = os.environ.get("POSTGRES_PASSWORD")
        db_port = os.environ.get("POSTGRES_PORT")

        while True:
            try:
                psycopg2.connect(dbname=db_name,
                                 user=db_user,
                                 password=db_password,
                                 host=db_host,
                                 port=db_port)
                break
            except psycopg2.OperationalError:
                time.sleep(1)
                continue

def wait_rabbitmq():
    # If we're in production, RabbitMQ is already running.
    if is_local_env():
        while True:
            try:
                QueueConnection()
                break
            except Exception as e:
                time.sleep(1)
                continue

def initialize_db():
    # Only automatically run migrations in prod.
    if not is_local_env():
        call_command("migrate", interactive=False)

# TODO: implement me! Run django sanity checks
def perform_checks():
    pass

from multiprocessing import cpu_count

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000

try:
    # We try to import Gunicorn. If we succeed, we define
    # the DjangoServer class to be a class that serves WSGI
    # apps using Gunicorn.
    from gunicorn.six import iteritems
    from gunicorn.app.base import Application
    
    class DjangoServer(Application):
        def __init__(self, **kwargs):
            global DEFAULT_HOST, DEFAULT_PORT
            self.options = {
                'accesslog': "-",
                'errorlog': "-",
                'disable_redirect_access_to_syslog': True,
                'workers': (cpu_count() * 2) + 1,
                'loglevel': 'info',
                'access_log_format': '%(t)s "%(m)s %(U)s%(q)s" %(s)s "%(a)s"',
                'bind': "{}:{}".format(kwargs.get('host', DEFAULT_HOST), kwargs.get('port', DEFAULT_PORT))
            }

            self.application = WSGIHandler()
            super().__init__()
        
        def load_config(self):
            config = dict([(key, value) for key, value in iteritems(self.options)
                           if key in self.cfg.settings and value is not None])
            for key, value in iteritems(config):
                self.cfg.set(key.lower(), value)
        
        def load(self):
            return self.application

        def run(self):
            try:
                super().run()
            except SystemExit:
                raise
            except:
                from bakround_applicant.utilities.sentry import forward_exception_to_sentry
                forward_exception_to_sentry()

except ImportError:
    # If we fail to import Gunicorn, it must not be installed,
    # let's define DjangoServer to use werkzeug instead.

    from werkzeug import run_simple, DebuggedApplication
    from werkzeug.serving import WSGIRequestHandler
    from bakround_applicant.utilities.logger import LoggerFactory

    class DjangoServer(object):
        def __init__(self, **kwargs):
            super().__init__()
            global DEFAULT_HOST, DEFAULT_PORT
            self.host = kwargs.get('host', DEFAULT_HOST)
            self.port = kwargs.get('port', DEFAULT_PORT)
            self.application = WSGIHandler()
            handler = self.get_staticfiles_handler()
            if handler:
                self.application = handler(self.application)

            if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
                self.application = DebuggedApplication(self.application, evalex=True, pin_security=False, pin_logging=False)

        def get_staticfiles_handler(self):
            from django.conf import settings
            try:
                if 'whitenoise.runserver_nostatic' in settings.INSTALLED_APPS:
                    return None
                elif 'django.contrib.staticfiles' in settings.INSTALLED_APPS:
                    from django.contrib.staticfiles.handlers import StaticFilesHandler
                    return StaticFilesHandler
                elif 'staticfiles' in settings.INSTALLED_APPS:
                    from staticfiles.handlers import StaticFilesHandler  # noqa
                    return StaticFilesHandler
                else:
                    return None
            except ImportError:
                return None

        def run(self):
            import logging
            import django
            from django.core.management.color import color_style
            from werkzeug._internal import _log
            import datetime

            os.environ['WERKZEUG_DEBUG_PIN'] = 'off'

            class RedirectHandler(logging.Handler):
                """Redirect logging sent to one logger (name) to another."""
                def __init__(self, level=logging.DEBUG):
                    super().__init__(level)
                    self.logger = LoggerFactory.create('')
                    self.level = level
            
                def emit(self, record):
                    self.logger.handle(record)

            # Redirect werkzeug log items
            werklogger = logging.getLogger('werkzeug')
            werklogger.setLevel(logging.DEBUG)
            werklogger.addHandler(RedirectHandler())
            werklogger.propagate = False

            _style = color_style()
            _orig_log = WSGIRequestHandler.log
        
            def werk_log(self, type, message, *args):
                time_str = datetime.datetime.now().strftime("%H:%M:%S:%f")
                try:
                    msg = '[{}] {}'.format(time_str, message % args)
                    http_code = str(args[1])
                except Exception:
                    return _orig_log(type, message, *args)
        
                # Utilize terminal colors, if available
                if http_code[0] == '2':
                    # Put 2XX first, since it should be the common case
                    msg = _style.HTTP_SUCCESS(msg)
                elif http_code[0] == '1':
                    msg = _style.HTTP_INFO(msg)
                elif http_code == '304':
                    msg = _style.HTTP_NOT_MODIFIED(msg)
                elif http_code[0] == '3':
                    msg = _style.HTTP_REDIRECT(msg)
                elif http_code == '404':
                    msg = _style.HTTP_NOT_FOUND(msg)
                elif http_code[0] == '4':
                    msg = _style.HTTP_BAD_REQUEST(msg)
                else:
                    # Any 5XX, or any other response
                    msg = _style.HTTP_SERVER_ERROR(msg)
        
                _log(type, msg)
        
            WSGIRequestHandler.log = werk_log

            from django_extensions.management.technical_response import null_technical_500_response
            from django.views import debug
            debug.technical_500_response = null_technical_500_response

            try:
                run_simple(self.host, self.port, self.application, use_debugger=True, use_reloader=True, request_handler=WSGIRequestHandler, threaded=True)
            except SystemExit:
                raise
            except:
                from bakround_applicant.utilities.sentry import forward_exception_to_sentry
                forward_exception_to_sentry()

