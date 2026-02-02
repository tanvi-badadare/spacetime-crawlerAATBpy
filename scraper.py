from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, urljoin, urldefrag

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    links = []

    if resp.status != 200 or resp.raw_response is None or resp.raw_response.content is None:
        '''
        if 600 <= resp.status <= 606:
            error_reason = resp.error 
        elif 400 <= resp.status <= 599 and resp.raw_response is not None:
            try:
                error_reason = resp.raw_response.content.decode('utf-8', errors='ignore')
            except Exception:
                error_reason = "Unable to decode content"
        else:
            error_reason = "Unknown error"
        '''
        return []
    
    try:
        soup = BeautifulSoup(resp.raw_response.content, "html.parser")
        for tag in soup.find_all("a", href=True):
            href = tag["href"].strip()
            if not href or href.startswith("#"):
                continue
            full_url = urljoin(url, href)
            clean_url, _ = urldefrag(full_url)
            links.append(clean_url)
    except Exception:
        return []
    
    return links
    
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    # what they had: return list()

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        url = url.rstrip("/")
        parsed = urlparse(url)

        # Scheme check
        if parsed.scheme not in {"http", "https"}:
            return False

        # Domain restriction
        allowed_domains = (
            "ics.uci.edu",
            "cs.uci.edu",
            "informatics.uci.edu",
            "stat.uci.edu",
        )

        netloc = parsed.netloc.lower().split(":")[0]
        if not any(netloc == domain or netloc.endswith("." + domain) for domain in allowed_domains):
            return False

        # Max URL length (crawler trap defense)
        if len(url) > 500:
            return False
        
        path = parsed.path.lower()
        query = parsed.query.lower()

        # File extension filtering
        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            r"|png|tiff?|mid|mp2|mp3|mp4"
            r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            r"|epub|dll|cnf|tgz|sha1"
            r"|thmx|mso|arff|rtf|jar|csv"
            r"|rm|smil|wmv|swf|wma|zip|rar|gz)$",
            parsed.path.lower()
        ):
            return False
        
        if re.search(r"/\d{4}/\d{1,2}(/\d{1,2})?/?$", path):
            return False
        if re.search(r"/(calendar|events?)/", path):
            return False
        
        if re.search(r"(year|month|week|day|page|sort|filter)=\d+", query):
            return False
        
        segments = [s for s in path.split("/") if len(s) > 2]
        counts = {}
        for s in segments:
            counts[s] = counts.get(s, 0) + 1
        if counts and max(counts.values()) > 2:
            return False

        return True

    except Exception:
        return False
