import re
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup
from collections import Counter


unique_urls = set()
word_counts = {}
all_words = Counter()
subdomains = {}

STOPWORDS = set([
    "a","about","above","after","again","against","all","am","an","and",
    "any","are","as","at","be","because","been","before","being","below",
    "between","both","but","by","could","did","do","does","doing","down",
    "during","each","few","for","from","further","had","has","have","having",
    "he","her","here","hers","herself","him","himself","his","how","i","if",
    "in","into","is","it","its","itself","let's","me","more","most","my","myself",
    "nor","of","on","once","only","or","other","ought","our","ours","ourselves",
    "out","over","own","same","she","should","so","some","such","than","that",
    "the","their","theirs","them","themselves","then","there","these","they",
    "this","those","through","to","too","under","until","up","very","was","we",
    "were","what","when","where","which","while","who","whom","why","with",
    "would","you","your","yours","yourself","yourselves"
])


def tokenize_text(text):
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


def scraper(url, resp):
    links = extract_next_links(url, resp)
    filtered_links = []

    for link in links:
        if is_valid(link):
            link, _ = urldefrag(link)
            filtered_links.append(link)
            unique_urls.add(link)

            netloc = urlparse(link).netloc.lower()
            if netloc.endswith(".ics.uci.edu"):
                if netloc not in subdomains:
                    subdomains[netloc] = set()
                subdomains[netloc].add(link)

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

        for tag in soup(["script", "style", "noscript"]):
            tag.extract()

        text = soup.get_text(separator=" ")
        words = [w for w in tokenize_text(text) if w not in STOPWORDS]

        word_counts[url] = len(words)
        all_words.update(words)

        for tag in soup.find_all("a", href=True):
            href = tag["href"].strip()
            if not href or href.startswith("#"):
                continue
            full_url = urljoin(url, href)
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
    """
    Decide whether to crawl this URL or not.
    Returns True if the URL is allowed, False otherwise.
    """
    try:
        parsed = urlparse(url)
        path = (parsed.path or "").lower()
        query = (parsed.query or "").lower()
        netloc = (parsed.netloc or "").lower()

        if parsed.scheme not in {"http", "https"}:
            return False

        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", path):
            return False

        allowed_domains = ("ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu")
        if not any(netloc == d or netloc.endswith("." + d) for d in allowed_domains):
            return False

        if re.search(r"/\d{4}/\d{1,2}(/\d{1,2})?/?$", path):
            return False

        if re.search(r"(year|month|week|day)=\d+", query):
            return False
        if "calendar" in path or "events" in path:
            return False

        if "machine-learning-databases" in path or "/ml/databases/" in path:
            return False

        segments = [s for s in path.split("/") if s]
        if len(segments) >= 2:
            counts = {}
            for seg in segments:
                counts[seg] = counts.get(seg, 0) + 1
            if max(counts.values()) > 2:
                return False

        if len(url) > 500:
            return False

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

        return True

    except Exception:
        return False
