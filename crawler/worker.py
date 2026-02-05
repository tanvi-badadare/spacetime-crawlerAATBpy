from threading import Thread

from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import analytics

class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        # basic check for requests in scraper
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
            if resp.status == 200 and resp.raw_response and resp.raw_response.content:
                try:
                    analytics.process_page(tbd_url, resp.raw_response.content)
                except Exception as e:
                    self.logger.error(f"Analytics processing failed for {tbd_url}: {e}")
            scraped_urls = scraper.scraper(tbd_url, resp)
            for scraped_url in scraped_urls:
                self.frontier.add_url(scraped_url)

            self.frontier.mark_url_complete(tbd_url)
