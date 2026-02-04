import re
from urllib.parse import urlparse, urljoin, urldefrag, urlunparse
from bs4 import BeautifulSoup
from collections import Counter

# Optional: Statistics tracking (can be disabled for thread-safety)
# Set ENABLE_STATS = False if running in multi-threaded environment
ENABLE_STATS = True

if ENABLE_STATS:
    unique_urls = set()
    word_counts = {}
    all_words = Counter()
    subdomains = {}

# from Aarabhi-edits - Stop words only in analytics.py; scraper imports from there
from analytics import STOP_WORDS as STOPWORDS


# from aarushi_edits1
def tokenize_text(text):
    """
    Tokenize text into words, filtering for ASCII alphabetic characters only.
    Returns a generator of lowercase tokens.
    """
    token = ''
    for char in text:
        if char.isascii() and char.isalpha():
            token += char.lower()
        else:
            if token:
                yield token
                token = ''
    if token:
        yield token


# from Aarabhi-edits
def normalize_url(url):
    """
    Normalize URL by removing query parameters, fragments, and trailing slashes.
    This helps avoid duplicate URLs with different query parameters.
    """
    parsed = urlparse(url)
    parsed = parsed._replace(query="", fragment="")
    normalized = urlunparse(parsed)
    if normalized.endswith("/"):
        normalized = normalized[:-1]
    return normalized


def scraper(url, resp):
    links = extract_next_links(url, resp)
    filtered_links = []
    
    for link in links:
        if is_valid(link):
            link, _ = urldefrag(link)
            filtered_links.append(link)
            
            # from aarushi_edits1 - Optional statistics tracking
            if ENABLE_STATS:
                unique_urls.add(link)
                netloc = urlparse(link).netloc.lower()
                if netloc not in subdomains:
                    subdomains[netloc] = set()
                subdomains[netloc].add(link)
    
    return filtered_links


def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    links = []

    if resp.status != 200 or resp.raw_response is None or resp.raw_response.content is None:
        # from Tanvi_edits
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
        soup = BeautifulSoup(resp.raw_response.content, "lxml")
        
        # from aarushi_edits1 - Remove script, style, and noscript tags to avoid extracting links from them
        for tag in soup(["script", "style", "noscript"]):
            tag.extract()
        
        # from aarushi_edits1 - Optional: Extract and tokenize text for statistics
        if ENABLE_STATS:
            text = soup.get_text(separator=" ")
            words = [w for w in tokenize_text(text) if w not in STOPWORDS]
            word_counts[url] = len(words)
            all_words.update(words)
        
        for tag in soup.find_all("a", href=True):
            href = tag["href"].strip()
            # from Aarabhi-edits - Filter javascript and mailto links
            if not href or href.startswith("#") or href.startswith("javascript:") or href.startswith("mailto:"):
                continue
            
            # from Aarabhi-edits - CRITICAL FIX: Use resp.url instead of url to handle redirects correctly
            absolute_url = urljoin(resp.url, href)
            clean_url, _ = urldefrag(absolute_url)
            # from Aarabhi-edits - Normalize URL to avoid duplicates with different query params
            clean_url = normalize_url(clean_url)
            
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
    """
    Decide whether to crawl this URL or not.
    Returns True if the URL is allowed, False otherwise.
    Combines the best validation rules from all team members' implementations.
    """
    try:
        # from aarushi_edits - Normalize URL by removing trailing slash
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

        # from aarushi_edits - Handle port numbers in netloc
        netloc_without_port = netloc.split(":")[0]
        if not netloc_without_port:
            return False
        if not any(netloc_without_port == domain or netloc_without_port.endswith("." + domain) for domain in allowed_domains):
            return False

        # from Tanvi_edits - Max URL length (crawler trap defense)
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
        
        # from Tanvi_edits - Date pattern filtering (avoid calendar/date URLs)
        if re.search(r"/\d{4}/\d{1,2}(/\d{1,2})?/?$", path):
            return False
        
        # from Tanvi_edits and aarushi_edits - Calendar and events filtering
        if re.search(r"/(calendar|events?)/", path):
            return False
        if re.search(r"/(events?|calendar)/\d", path):
            return False
        
        # from Tanvi_edits and aarushi_edits - Query parameter filtering (avoid date-based queries and pagination)
        if re.search(r"(year|month|week|day|page|sort|filter)=\d+", query):
            return False
        
        # from Tanvi_edits - Machine learning databases filtering
        if "machine-learning-databases" in path or "/ml/databases/" in path:
            return False
        
        # from aarushi_edits1 - Additional filters
        if "ical" in query or "ical" in path:
            return False
        if "intranet.ics.uci.edu" in netloc:
            return False
        if "doku.php" in path:
            return False
        if "do=media" in query or "image=" in query:
            return False
        if query.count("&") >= 3:
            return False
        
        # from aarushi_edits - Segment repetition detection (crawler trap defense) - improved to only count segments > 2 chars
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
