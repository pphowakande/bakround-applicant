__author__ = "natesymer"

"""
Implements a safe browser interface that helps prevent getting
accounts banned. Each browser contains a tor proxy and a headless
chrome instance. The ports Tor uses are randomized, and the password
used to connect to the tor controller is randomized.
"""

from functools import reduce, partial

import json
import socket
import time
import sys
import time
import decimal
import random
import subprocess
import socket
from uuid import uuid4

from stem.process import launch_tor_with_config
from stem.control import Controller
from stem import Signal

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.command import Command
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, NoSuchAttributeException, WebDriverException, JavascriptException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from bakround_applicant.utilities.logger import LoggerFactory

# Prevent Selenium from logging extraneous internal details.
import logging
from selenium.webdriver.remote.remote_connection import LOGGER
LOGGER.setLevel(logging.WARNING)
##############################################################

CHROME_WIDTH = 200
CHROME_HEIGHT = 300


def get_port(start, end):
    port = None
    while True:
        port = random.randint(start, end)
        if port in [9222, 9050, 9051]:  # No default ports please!
            continue

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        if result != 0:
            break
    return port


class BrowserRecoverableError(Exception):
    pass


class BrowserFatalError(Exception):
    pass


class Browser(object):
    USER_AGENT = "Mozilla/6.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100-r0 Safari/537.36"

    def __init__(self,
                 cookie_predicate=None, # Used to filter cookies before setting href
                 resets_ip=True, # Whether or not to reset IP before setting href
                 uses_tor=True):
        super().__init__()

        self.identifier = uuid4().hex
        self.logger = LoggerFactory.create("BROWSER_{}".format(self.identifier))

        self.uses_tor = uses_tor
        self.resets_ip = resets_ip
        self.cookie_predicate = cookie_predicate  # Predicate to filter cookies
        self._last_wakes = {}
        self.driver = None
        self.tor_process = None
        self.port = None
        self.control_port = None
        self.open()

    def open(self):
        if self.uses_tor:
            self._create_tor_proxy()
        self._create_browser_instance(self.port)
        return self

    def __del__(self):
        self.close()

    def close(self):
        """Closes the browser"""
        if self.driver:
            self.driver.close()
        if self.tor_process:
            self.tor_process.kill()

        self.driver = None
        self.tor_process = None
        self.port = None
        self.control_port = None
        return self

    def reset(self):
        """Resets the Browser instance"""
        return self.close() and self.open()

    @property
    def is_open(self):
        try:
            self.driver.execute(Command.STATUS)
            return True
        except (socket.error):
            return False

    @property
    def log_entries(self):
        return self.driver.get_log('browser')

    def reset_ip(self):
        """Gets a new IP address for the browser."""
        if self.tor_process:
            with Controller.from_port(port=self.control_port) as controller:
                controller.authenticate()
                wait = controller.get_newnym_wait()
                if wait > 0:
                    time.sleep(wait)
                controller.signal(Signal.NEWNYM)
                self.logger.info("Reset IP address.")

    @property
    def page_source(self):
        return self._harden(func=lambda: self.driver.page_source or "")

    @property
    def title(self):
        return self._harden(func=lambda: self.driver.title or "")

    @property
    def href(self):
        return self._harden(func=lambda: self.driver.current_url or "")

    @href.setter
    def href(self, value):
        self._wait_for_tor()
        self.filter_cookies()
        if self.resets_ip and not self.cookies:
            self.reset_ip()
        self._sleep_since(key=self.identifier)
        self.filter_cookies()

        self._ensure_safety()
        self._harden(func=lambda: self.driver.get(value),
                     reset_on_timeout=False)
        self.filter_cookies()

    @property
    def cookies(self):
        return self._harden(func=lambda: self.driver.get_cookies() or None)

    @cookies.setter
    def cookies(self, value):
        def go():
            self.driver.delete_all_cookies()

            for c in value:
                self.driver.add_cookie(c)

        self._harden(func=go)

    @cookies.deleter
    def cookies(self):
        self._harden(self.driver.delete_all_cookies)

    @property
    def cookies_enabled(self):
        return self._harden(func=lambda: self.driver.cookies_enabled)

    @cookies_enabled.setter
    def cookies_enabled(self, value):
        def go():
            self.driver.cookies_enabled = value
        self._harden(func=go)

    def filter_cookies(self):
        cs = self.cookies

        def go():
            self.driver.delete_all_cookies()
            if cs:
                if not self.cookie_predicate:
                    for c in cs:
                        self.driver.add_cookie(c)
                else:
                    for c in filter(self.cookie_predicate, cs):
                        self.driver.add_cookie(c)
        self._harden(func=go)

    def xpath(self, q, **kwargs):
        """Not real xpath - doesn't support selecting text, html, etc. Finds element(s)
           by XPath. Raises browser warnings if the element is not found."""
        return self._finder(q, By.XPATH, **kwargs)

    def selector(self, sel, **kwargs):
        """Find element(s) by CSS selector. Raises browser warnings if the element is not found."""
        return self._finder(sel, By.CSS_SELECTOR, **kwargs)

    def execute(self, *args):
        return self.driver.execute_script(*args)

    def scroll_to(self, element):
        self.driver.execute_script("arguments[0].scrollIntoView();", element)

    #
    # PRIVATE API
    #

    def _finder(self, sel, by, wait=None, scope=None, many=False, visible=False, required=False, nothrow=False):
        """Find element(s). Raises browser warnings based on what happens."""
        options = Options()

        # Start in a new window, separate from other instances.
        # This is vital to our privacy.
        options.add_argument("--new-window")

        # Headlessness
        options.add_argument("--window-size={},{}".format(CHROME_WIDTH, CHROME_HEIGHT))
        options.add_argument("--start-maximized")  # Start maximized
        options.add_argument("--headless")  # Run Chrome in Headless mode
        options.add_argument("--disable-gpu")  # Disable GPU rendering
        options.add_argument("--disable-software-rasterizer")  # Disable CPU rendering
        options.add_argument("--no-sandbox")
        options.add_argument('--disable-dev-shm-usage')

        d = DesiredCapabilities.CHROME
        d['loggingPrefs'] = {'browser': 'ALL'}

        driver1 = webdriver.Chrome(chrome_options= options,desired_capabilities=d)
        driver1.get(self.href)

        self.driver = driver1
        el = self.driver
        # finder function calls find to get all elements from that class
        f = self._find(by, sel, many, visible, nothrow)
        wait = 10
        go = (lambda: WebDriverWait(el, wait).until(f)) #if wait else partial(f, el)
        try:
            return self._harden(func=go, finding_element=True)
        except (NoSuchElementException, NoSuchAttributeException, TimeoutException):
            if nothrow:
                return None
            if required:
                raise BrowserFatalError()
            else:
                self.reset()
                raise BrowserRecoverableError()

    def _find(self, by, q, many, visible, nothrow):
        """Returns a function that can be used to find elements in a page inside Selenium."""

        # Determine the correct expected condition to wrap
        if many:
            ec = EC.visibility_of_all_elements_located if visible else EC.presence_of_all_elements_located
        else:
            ec = EC.visibility_of_element_located if visible else EC.presence_of_element_located

        # Wrap it
        f = None

        if type(q) is list:  # We have a list of queries, or them together.
            # NOTA BENE: We can't just comma separate the queries because this is generic and should support CSS Selectors & XPATHs
            if not q:
                def f(_): return False
            else:
                def f(d): return reduce(lambda acc, v: acc or ec((by, v))(d), q, False)
        else:
            f = ec((by, q))  # Just use the original expected condition.

        if not f:
            raise Exception("Browser#_find: Programming Error: f is None")

        return f

    def _harden(self, func, reset_on_timeout=True, fatal_on_exception=True, finding_element=False):
        """Handles any Selenium WebDriver errors that occur when evaluating func()"""
        try:
            return func()
        except WebDriverException:
            ename = sys.exc_info()[0].__name__

            # Page interaction:
            # ElementClickInterceptedException
            # InvalidElementStateException

            if ename == 'ErrorInResponseException':
                self.logger.info("Encountered internal server error.")
                self.reset()
                raise BrowserRecoverableError()
            if ename in ['StaleElementReferenceException', 'InvalidSwitchToTargetException', 'InvalidSessionIdException']:
                self.reset()
                raise BrowserRecoverableError()
            elif ename == 'TimeoutException':
                if finding_element:
                    raise NoSuchElementException()
                else:
                    if reset_on_timeout:
                        self.reset()
                    raise BrowserRecoverableError()
            elif fatal_on_exception:
                raise BrowserFatalError()
            else:
                raise

    def _sleep_since(self, n=2, prec=10000, key="default"):
        """Ensures there's between n and 2n seconds between calls, between n^3 and 2n^3 seconds if authenticated."""

        if self.cookies:  # If we're authenticated on the current page, wait longer
            if n <= 1:
                n = 12.5  # Ensure we're waiting long enough
            else:
                n = n * n * n

        wait_time = decimal.Decimal(random.randrange(
            n * prec, n * 2 * prec)) / decimal.Decimal(prec)

        if self._last_wakes:
            wait_time -= decimal.Decimal(time.time()) - decimal.Decimal(self._last_wakes[key])
        else:
            self._last_wakes = {}

        if wait_time > 0:
            time.sleep(wait_time)

        self._last_wakes[key] = decimal.Decimal(time.time())

    def _wait_for_tor(self):
        """Wait until Tor can process traffic."""
        if self.tor_process:
            total_wait_time = 0
            with Controller.from_port(port=self.control_port) as controller:
                controller.authenticate()
                wait_interval = 0.5
                if not controller.is_alive():
                    self.logger.info("Waiting for Tor to come online...")
                    tries = 0
                    while not controller.is_alive():
                        time.sleep(wait_interval)
                        tries += 1
                        if tries > 10:
                            raise BrowserRecoverableError()

    def _create_tor_proxy(self):
        while True:
            try:
                self.port = get_port(9000, 9999)
                self.control_port = get_port(9000, 9999)

                self.logger.info("Attempting to open Tor proxy (socks: {}, control: {})".format(
                    self.port, self.control_port))

                self.tor_process = launch_tor_with_config(
                    config={
                        'SocksPort': str(self.port),
                        'ControlPort': str(self.control_port),
                        'ExitNodes': '{us}', # Only use USA IP's - Avoid looking like offshore mining.
                        'SafeSocks': '1',
                        'CookieAuthentication': '1',  # We want cookie auth
                        'DataDirectory': '/var/lib/tor/{}'.format(self.identifier)
                    }
                    # We can't use a timeout UNLESS we're calling from the main thread.
                    #timeout = 20
                )
                break
            except OSError as e:
                continue

    def devtools(self, cmd, params={}):
        """Calls a devtools command, return tha result."""
        resource = "/session/%s/chromium/send_command_and_get_result" % self.driver.session_id
        url = self.driver.command_executor._url + resource
        body = json.dumps({'cmd': cmd, 'params': params})
        response = self.driver.command_executor._request('POST', url, body)
        if response['status']:
            raise BrowserRecoverableError()
        return response.get('value')

    def _set_js_enabled(self, enabled):
        self.devtools("Emulation.setScriptExecutionDisabled", {"disabled": not enabled})

    def _ensure_safety(self):
        # If we find we need to block certain URLs, add them!
        #self.devtools("Network.setBlockedURLs", {"urls": []})
        try:
            self.devtools("Page.addScriptToEvaluateOnNewDocument", {"source": INJECT_JS})
        except JavascriptException:
            self.logger.info("Failed to inject counter-anti-scraping JS into headless browser.")
            raise BrowserFatalError()
        self.devtools("Network.setExtraHTTPHeaders", {"headers": {"DNT": "1"}})

        global CHROME_WIDTH
        global CHROME_HEIGHT
        self.driver.set_window_size(CHROME_WIDTH, CHROME_HEIGHT)

    def _create_browser_instance(self, socks_port=9050):
        global CHROME_WIDTH
        global CHROME_HEIGHT
        self.logger.info("Creating headless browser instance")

        try:
            options = Options()
            if self.uses_tor:
                options.add_argument("--disable-infobars")  # Disable info bars
                options.add_argument("--disable-extensions")  # Disable Chrome extensions
                options.add_argument("--disable-plugins-discovery")  # Disable Plugins discovery
                options.add_argument("--disable-pepper-3d")  # Disable Flash
                options.add_argument("--disable-flash-3d")  # Disable Flash
                options.add_argument("--disable-flash-stage3d")  # Disable Flash
                options.add_argument("--disable-bundled-ppapi-flash")  # Disable Flash

            # Misc
            if self.uses_tor:
                options.add_argument("--disable-background-networking")
                options.add_argument("--disable-default-apps")

            # Logging
            # This enables us to read console messages using the DevTools.
            options.add_argument("--enable-logging")
            options.add_argument("--v=1")

            # Disable things that could get us caught
            options.add_argument("--disable-sync")
            options.add_argument("--no-first-run")

            # Start in a new window, separate from other instances.
            # This is vital to our privacy.
            options.add_argument("--new-window")

            # Headlessness
            options.add_argument("--window-size={},{}".format(CHROME_WIDTH, CHROME_HEIGHT))
            options.add_argument("--start-maximized")  # Start maximized
            options.add_argument("--headless")  # Run Chrome in Headless mode
            options.add_argument("--disable-gpu")  # Disable GPU rendering
            options.add_argument("--disable-software-rasterizer")  # Disable CPU rendering
            options.add_argument("--no-sandbox")
            if self.uses_tor:
                options.add_argument("--disable-webgl")  # Disable WebGL

            # Use Tor through a SOCKS5 proxy
            if self.uses_tor:
                options.add_argument("--proxy-server=socks://localhost:{}".format(socks_port))

            # Tell Chrome we're American
            options.add_argument("--network-country-iso=US")
            options.add_argument("--lang=en_US")

            # Lie about our user agent
            options.add_argument("--user-agent=\"{}\"".format(self.USER_AGENT))

            # Give it a place to store user stuff. This helps us pass
            # a couple headlessness tests.
            options.add_argument("--user-data-dir=/chromeconfig/Default")

            d = DesiredCapabilities.CHROME
            d['loggingPrefs'] = {'browser': 'ALL'}

            self.driver = webdriver.Chrome(chrome_options=options, desired_capabilities=d)
        except OSError as e:
            self.logger.error("probably ran out of memory.")
            raise BrowserRecoverableError()

# The code below is injected into the browser before it loads any page.
# This is accomplished via the Chromium DevTools API.
#
# We could have put this in a chrome plugin, but that's less self-contained
# and would have required us to use "headful" chromium.

# Running the tests for this browser:
# $ TEST_CMD=./test_scripts/screen_scrape.py file:///app/test_scripts/test_browser.html
# $ docker-compose exec worker $TEST_CMD
INJECT_JS = """
(function() {

// Configuration
const mockImageDimension = 20; // arbitrary non-zero number
const mockLanguages = ['en-US', 'en', 'und']; // UND is the
const mockPlugins = [{}, {}]; // only needs to have `length > 0`, but we could mock the plugins too
const mockChromeProperty = {
    runtime: {"PlatformOs":{"MAC":"mac","WIN":"win","ANDROID":"android","CROS":"cros","LINUX":"linux","OPENBSD":"openbsd"},"PlatformArch":{"ARM":"arm","X86_32":"x86-32","X86_64":"x86-64","MIPS":"mips","MIPS64":"mips64"},"PlatformNaclArch":{"ARM":"arm","X86_32":"x86-32","X86_64":"x86-64","MIPS":"mips","MIPS64":"mips64"},"RequestUpdateCheckStatus":{"THROTTLED":"throttled","NO_UPDATE":"no_update","UPDATE_AVAILABLE":"update_available"},"OnInstalledReason":{"INSTALL":"install","UPDATE":"update","CHROME_UPDATE":"chrome_update","SHARED_MODULE_UPDATE":"shared_module_update"},"OnRestartRequiredReason":{"APP_UPDATE":"app_update","OS_UPDATE":"os_update","PERIODIC":"periodic"}},
    csi: () => undefined,
    loadTimes: () => undefined,
    app: {
        isInstalled: true
    },
    webstore: {
        install: (url, onSuccess, onFailure) => undefined,
        onDownloadProgress: {},
        onInstallStateChanged: {}
    }
};

function patchWindow(w) {
    //
    // Pass the "Chrome" test

    w.chrome = mockChromeProperty;

    return w;
}

patchWindow(window);

//
// Pass the "Languages" test

Object.defineProperty(Navigator.prototype, 'languages', {
    get: () => mockLanguages
});

Object.defineProperty(navigator, 'languages', {
    get: () => mockLanguages
});

//
// Pass the "Plugins" test

Object.defineProperty(Navigator.prototype, 'plugins', {
    get: () => mockPlugins
});

Object.defineProperty(navigator, 'plugins', {
    get: () => mockPlugins
});

//
// Pass the "WebDriver" test

if (Navigator.prototype.webdriver) {
    delete Navigator.prototype.webdriver;
}

if (navigator.webdriver) {
    delete navigator.webdriver;
}

//
// Pass the "WebGL" test

const getParameter = WebGLRenderingContext.getParameter;
WebGLRenderingContext.prototype.getParameter = function(parameter) {
    if (parameter === 37445) return 'Intel Open Source Technology Center';
    else if (parameter === 37446) return 'Mesa DRI Intel(R) Ivybridge Mobile ';
    return getParameter(parameter);
};

//
// Pass all permissions tests
// The notification permissions prompt could stymie Screen Scraping

const oldQuery = Permissions.prototype.query;
Permissions.prototype.query = function(ps) {
    return ps.name === 'notifications' ? Promise.resolve({ state: Notification.permission }) : oldQuery(ps);
}

//
// Pass all the window-based tests in iFrames

let contentWindow = Object.getOwnPropertyDescriptor(HTMLIFrameElement.prototype, 'contentWindow');
Object.defineProperty(HTMLIFrameElement.prototype, 'oldContentWindow', {...contentWindow, configurable: true });
Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
    ...contentWindow,
    configurable: true,
    get: function() { return patchWindow(this.oldContentWindow); }
});

})();
"""
