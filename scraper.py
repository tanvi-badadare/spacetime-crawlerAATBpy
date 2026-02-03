import re
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    links = []

    if resp.status != 200 or resp.raw_response is None or resp.raw_response.content is None:
        if 600 <= resp.status <= 606:
            error_reason = resp.error if resp.error else f"Cache error ({resp.status})"
        elif 400 <= resp.status <= 599:
            if resp.raw_response and hasattr(resp.raw_response, "reason_phrase"):
                error_reason = f"HTTP {resp.status} {resp.raw_response.reason_phrase}"
            else:
                error_reason = f"HTTP {resp.status}"
        else:
            error_reason = "No response" if resp.raw_response is None else "Unknown error"

        print(f"Error fetching url: {url}, status: {resp.status}, reason: {error_reason}")
        return links
    
    try:
        soup = BeautifulSoup(resp.raw_response.content, "html.parser")
        
        # Remove script, style, and noscript tags to avoid extracting links from them
        for tag in soup(["script", "style", "noscript"]):
            tag.extract()
        
        for tag in soup.find_all("a", href=True):
            href = tag["href"].strip()
            if not href or href.startswith("#") or href.startswith("javascript:") or href.startswith("mailto:"):
                continue
            
            # CRITICAL FIX: Use resp.url instead of url to handle redirects correctly
            full_url = urljoin(resp.url, href)
            clean_url, _ = urldefrag(full_url)
            links.append(clean_url)
    except Exception as e:
        print(f"Error parsing {url}: {e}")
    
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
        # Normalize URL by removing trailing slash
        url = url.rstrip("/")
        parsed = urlparse(url)

        path = (parsed.path or "").lower()
        query = (parsed.query or "").lower()
        netloc = (parsed.netloc or "").lower()

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

        # Handle port numbers in netloc
        netloc_without_port = netloc.split(":")[0]
        if not netloc_without_port:
            return False
        if not any(netloc_without_port == domain or netloc_without_port.endswith("." + domain) for domain in allowed_domains):
            return False

        # Max URL length (crawler trap defense)
        max_len = 500
        if len(url) > max_len:
            return False
        
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
            path
        ):
            return False
        
        # Date pattern filtering (avoid calendar/date URLs)
        if re.search(r"/\d{4}/\d{1,2}(/\d{1,2})?/?$", path):
            return False
        
        # Calendar and events filtering
        if re.search(r"/(calendar|events?)/", path):
            return False
        if re.search(r"/(events?|calendar)/\d", path):
            return False
        
        # Query parameter filtering (avoid date-based queries and pagination)
        if re.search(r"(year|month|week|day|page|sort|filter)=\d+", query):
            return False
        
        # Machine learning databases filtering
        if "machine-learning-databases" in path or "/ml/databases/" in path:
            return False
        
        # Segment repetition detection (crawler trap defense)
        segments = [s for s in path.split("/") if s and len(s) > 2]
        if len(segments) >= 2:
            counts = {}
            for seg in segments:
                counts[seg] = counts.get(seg, 0) + 1
            if max(counts.values()) > 2:
                return False

        return True

    except Exception:
        return False
    
    
