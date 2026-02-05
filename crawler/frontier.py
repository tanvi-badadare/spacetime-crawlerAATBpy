import os
import shelve
import time

from threading import RLock
from queue import Queue, Empty
from urllib.parse import urlparse

from utils import get_logger, get_urlhash, normalize
from scraper import is_valid


class Frontier(object):
    """Thread-safe frontier: Queue for URLs, RLock for shelve."""

    def __init__(self, config, restart):
        self.logger = get_logger("FRONTIER")
        self.config = config
        self._lock = RLock()
        self.url_queue = Queue()
        self.pages_completed = 0
        self._urls_in_progress = 0
        self._domain_last_request = {}  # domain -> last request time (for per-domain politeness)
        self._politeness_delay = getattr(config, 'time_delay', 0.5)

        if not os.path.exists(self.config.save_file) and not restart:
            self.logger.info(
                f"Did not find save file {self.config.save_file}, "
                f"starting from seed.")
        elif os.path.exists(self.config.save_file) and restart:
            self.logger.info(
                f"Found save file {self.config.save_file}, deleting it.")
            os.remove(self.config.save_file)

        self.save = shelve.open(self.config.save_file)
        if restart:
            for url in self.config.seed_urls:
                url = url.strip()
                self.add_url(url)
        else:
            self._parse_save_file()
            if not self.save:
                for url in self.config.seed_urls:
                    url = url.strip()
                    self.add_url(url)

    def _parse_save_file(self):
        total_count = len(self.save)
        tbd_count = 0
        self.pages_completed = 0
        with self._lock:
            for url, completed in self.save.values():
                if completed:
                    self.pages_completed += 1
                if not completed and is_valid(url):
                    self.url_queue.put(url)
                    tbd_count += 1
        self.logger.info(
            f"Found {tbd_count} urls to be downloaded from {total_count} "
            f"total urls discovered.")

    def get_tbd_url(self, timeout=1.0):
        """Thread-safe: block until URL available or timeout. Returns None on timeout."""
        if self.is_done():
            return None
        try:
            url = self.url_queue.get(timeout=timeout)
            with self._lock:
                self._urls_in_progress += 1
            return url
        except Empty:
            return None

    def is_done(self):
        """True only when frontier is exhausted: queue empty and no URLs in progress. No page limit."""
        with self._lock:
            return self.url_queue.empty() and self._urls_in_progress == 0

    def get_domain(self, url):
        """Extract domain (host) from URL for per-domain politeness."""
        return urlparse(url).netloc.split(':')[0].lower() or ''

    def wait_for_politeness(self, domain):
        """Block until at least politeness_delay (e.g. 500ms) has passed since last request to this domain.
        Two or more requests to the same domain (from any thread) will always be at least 500ms apart."""
        with self._lock:
            now = time.time()
            last = self._domain_last_request.get(domain, 0)
            need = max(0.0, self._politeness_delay - (now - last))
        time.sleep(need)
        with self._lock:
            self._domain_last_request[domain] = time.time()

    def add_url(self, url):
        url = normalize(url)
        urlhash = get_urlhash(url)
        with self._lock:
            if urlhash not in self.save:
                self.logger.info(f"Adding URL to Frontier: {url}")
                self.save[urlhash] = (url, False)
                self.save.sync()
                self.url_queue.put(url)

    def mark_url_complete(self, url):
        with self._lock:
            self._urls_in_progress -= 1
            self.pages_completed += 1
            urlhash = get_urlhash(url)
            if urlhash not in self.save:
                self.logger.error(
                    f"Completed url {url}, but have not seen it before.")
            self.save[urlhash] = (url, True)
            self.save.sync()
