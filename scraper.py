import re
from urllib.parse import urlparse, urljoin, urldefrag, urlunparse
from bs4 import BeautifulSoup

def scraper(url, resp):  
    links = extract_next_links(url, resp)
    print(f"Scraped {url} -> {len(links)} valid links")
    return links

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content

    links = set()

    if resp.status != 200 or resp.raw_response is None or resp.raw_response.content is None:
        print(f"[SCRAPER] Skipping {url}, status {resp.status}")
        return links
    
    soup = BeautifulSoup(resp.raw_response.content, "lxml")
    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get('href').strip()

        if href.startswith("#") or href.startswith("javascript:") or href.startswith("mailto:") or href == "":
            continue

        absolute_url = urljoin(resp.url, href)
        clean_url = urldefrag(absolute_url).url
        clean_url = normalize_url(clean_url)

        if is_valid(clean_url):
            links.add(clean_url)

    return list(links)

def normalize_url(url):
    parsed = urlparse(url)
    parsed = parsed._replace(query="", fragment="")
    normalized = urlunparse(parsed)
    if normalized.endswith("/"):
        normalized = normalized[:-1]
    return normalized

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return False
        
        allowed_domains = (
            "ics.uci.edu",
            "cs.uci.edu",
            "informatics.uci.edu",
            "stat.uci.edu"
        )
        if not any(parsed.netloc.endswith(domain) for domain in allowed_domains):
            return False
        
        path = parsed.path.lower()    
        if re.search(r"/(calendar|events)/", path):
            return False
        if "archive.ics.uci.edu" in url.lower():
            return False
        
        return not re.search(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", path
        )
    except TypeError:
        return False
