import threading
from threading import Thread

from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import analytics

CONTENT_STATS_LOG = "content_stats_log.txt"
_content_stats_lock = threading.Lock()

# Skip processing files >= 2MB to avoid wasting resources on large non-HTML files
MAX_CONTENT_SIZE_BYTES = 2 * 1024 * 1024  # 2 MB


def _log_content_stats(url, size_bytes):
    with _content_stats_lock:
        with open(CONTENT_STATS_LOG, "a", encoding="utf-8") as f:
            if f.tell() == 0:
                f.write("url\tsize_bytes\n")
            f.write(f"{url}\t{size_bytes}\n")


class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)
        
    def run(self):
        while True:
            tbd_url = self.frontier.get_tbd_url(timeout=1.0)
            if not tbd_url:
                if self.frontier.is_done():
                    self.logger.info("Crawl limit reached. Stopping.")
                    break
                continue
            domain = self.frontier.get_domain(tbd_url)
            self.frontier.wait_for_politeness(domain)
            resp = download(tbd_url, self.config, self.logger)
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            scraped_urls = []
            if resp.status == 200 and resp.raw_response and resp.raw_response.content:
                content = resp.raw_response.content
                size_bytes = len(content)
                # Skip large files - don't process or extract links from them
                if size_bytes >= MAX_CONTENT_SIZE_BYTES:
                    self.logger.info(
                        f"Skipped {tbd_url} (size {size_bytes} bytes >= {MAX_CONTENT_SIZE_BYTES} limit)")
                else:
                    try:
                        _log_content_stats(tbd_url, size_bytes)
                    except Exception as e:
                        self.logger.error(f"Content stats logging failed for {tbd_url}: {e}")
                    try:
                        analytics.process_page(tbd_url, content)
                    except Exception as e:
                        self.logger.error(f"Analytics processing failed for {tbd_url}: {e}")
                    scraped_urls = scraper.scraper(tbd_url, resp)
            for scraped_url in scraped_urls:
                self.frontier.add_url(scraped_url)

            self.frontier.mark_url_complete(tbd_url)
