import re
from urllib.parse import urlparse, urljoin, urldefrag, urlunparse
from bs4 import BeautifulSoup

_URL_SEPARATORS = re.compile(r"\s+")


def normalize_url(url):
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

    return filtered_links


def extract_next_links(url, resp):
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
        soup = BeautifulSoup(resp.raw_response.content, "lxml")
        for tag in soup(["script", "style", "noscript"]):
            tag.extract()

        for tag in soup.find_all("a", href=True):
            href_raw = tag["href"].strip()
            if not href_raw:
                continue

            for part in _URL_SEPARATORS.split(href_raw):
                href = part.strip()
                if not href or href.startswith("#") or href.startswith("javascript:") or href.startswith("mailto:"):
                    continue

                href = href.replace("https|", "https:").replace("http|", "http:")
                absolute_url = urljoin(resp.url, href)
                clean_url, _ = urldefrag(absolute_url)
                clean_url = normalize_url(clean_url)

                links.append(clean_url)
    except Exception as e:
        print(f"Error parsing {url}: {e}")

    return list(set(links))


def is_valid(url):
    try:
        url = url.rstrip("/")
        parsed = urlparse(url)

        path = (parsed.path or "").lower()
        query = (parsed.query or "").lower()
        netloc = (parsed.netloc or "").lower()

        if parsed.scheme not in {"http", "https"}:
            return False

        allowed_domains = (
            "ics.uci.edu",
            "cs.uci.edu",
            "informatics.uci.edu",
            "stat.uci.edu",
        )

        netloc_without_port = netloc.split(":")[0]
        if not netloc_without_port:
            return False
        if not any(netloc_without_port == domain or netloc_without_port.endswith("." + domain) for domain in allowed_domains):
            return False

        max_len = 500
        if len(url) > max_len:
            return False
        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            r"|png|tiff?|mid|mp2|mp3|mp4"
            r"|wav|avi|mov|mpeg|mpg|ram|m4v|mkv|ogg|ogv|pdf"
            r"|ps|eps|tex|ppt|pptx|ppsx|doc|docx|xls|xlsx|names"
            r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            r"|epub|dll|cnf|tgz|sha1"
            r"|thmx|mso|arff|rtf|jar|csv"
            r"|rm|smil|wmv|swf|wma|zip|rar|gz)$",
            path
        ):
            return False
        if re.search(r"/\d{4}/\d{1,2}(/\d{1,2})?/?$", path):
            return False
        if re.search(r"/(calendar|events?)/", path):
            return False
        if re.search(r"/(events?|calendar)/\d", path):
            return False
        if re.search(r"(year|month|week|day|page|sort|filter)=\d+", query):
            return False
        if "machine-learning-databases" in path or "/ml/databases/" in path:
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
