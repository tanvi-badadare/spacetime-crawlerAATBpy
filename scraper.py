import re
from urllib.parse import urlparse, urljoin
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
            error_reason = resp.error 
        elif 400 <= resp.status <= 599 and resp.raw_response is not None:
            try:
                error_reason = resp.raw_response.content.decode('utf-8', errors='ignore')
            except Exception:
                error_reason = "Unable to decode content"
        else:
            error_reason = "Unknown error"

        print(f"Error fetching url: {error_reason}")
        return links
    
    try:
        soup = BeautifulSoup(resp.raw_response.content, "html.parser")
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
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())
        
        allowed = (
            "ics.uci.edu",
            "cs.uci.edu",
            "informatics.uci.edu",
            "stat.uci.edu",
        )

        max_len = 500

        if len(url) > max_len:
            return False
        
        netloc = (parsed.netloc or "").lower()
        if not netloc:
            return False
        if not any(netloc == d or netloc.endswith("." + d) for d in allowed):
            return False
        
        if re.search(r"/\d{4}/\d{1,2}(/\d{1,2})?/?$", path):
            return False
        if re.search(r"/(events?|calendar)/\d", path):
            return False
        if re.search(r"(year|month|week|day)=\d+", query):
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

        return True


    except TypeError:
        print ("TypeError for ", parsed)
        raise
    
    
