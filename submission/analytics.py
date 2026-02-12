import threading
from tokenizer import tokenize_text, computeWordFrequencies
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from duplicate_detector import DuplicateDetector

DUPLICATES_LOG = "duplicates_log.txt"
_duplicates_lock = threading.Lock()
_analytics_lock = threading.Lock()

# Near-duplicate detection using shingle-based fingerprinting
_duplicate_detector = DuplicateDetector(k_shingle=3, fingerprint_size=20, similarity_threshold=0.5)

# Skip pages with too few words
MIN_WORD_COUNT = 50

STOP_WORDS = {
    "a","able","about","above","abst","across","after","again","against","all",
    "almost","alone","along","already","also","although","always","am","among",
    "amongst","amoungst","amount","an","and","another","any","anyhow","anyone",
    "anything","anyway","anywhere","are","around","as","at","back","be","became",
    "because","become","becomes","becoming","been","before","beforehand","behind",
    "being","below","beside","besides","between","beyond","bill","both","bottom",
    "but","by","call","can","cannot","cant","co","con","could","couldnt","cry",
    "de","describe","detail","do","done","down","due","during","each","eg","eight",
    "either","eleven","else","elsewhere","empty","enough","etc","even","ever",
    "every","everyone","everything","everywhere","except","few","fifteen","fifty",
    "fill","find","fire","first","five","for","former","formerly","forty","found",
    "four","from","front","full","further","get","give","go","had","has","hasnt",
    "have","he","hence","her","here","hereafter","hereby","herein","hereupon",
    "hers","herself","him","himself","his","how","however","hundred","i","ie","if",
    "in","inc","indeed","interest","into","is","it","its","itself","keep","last",
    "latter","latterly","least","less","ltd","made","many","may","me","meanwhile",
    "might","mill","mine","more","moreover","most","mostly","move","much","must",
    "my","myself","name","namely","neither","never","nevertheless","next","nine",
    "no","nobody","none","noone","nor","not","nothing","now","nowhere","of","off",
    "often","on","once","one","only","onto","or","other","others","otherwise","our",
    "ours","ourselves","out","over","own","part","per","perhaps","please","put",
    "rather","re","same","see","seem","seemed","seeming","seems","serious","several",
    "she","should","show","side","since","sincere","six","sixty","so","some",
    "somehow","someone","something","sometime","sometimes","somewhere","still",
    "such","system","take","ten","than","that","the","their","them","themselves",
    "then","thence","there","thereafter","thereby","therefore","therein","thereupon",
    "these","they","thick","thin","third","this","those","though","three","through",
    "throughout","thru","thus","to","together","too","top","toward","towards","twelve",
    "twenty","two","un","under","until","up","upon","us","very","via","was","we",
    "well","were","what","whatever","when","whence","whenever","where","whereafter",
    "whereas","whereby","wherein","whereupon","wherever","whether","which","while",
    "whither","who","whoever","whole","whom","whose","why","will","with","within",
    "without","would","yet","you","your","yours","yourself","yourselves",
    "january","february","march","april","may","june","july",
    "august","september","october","november","december"
}


unique_pages = set()
global_word_frequencies = {}
longest_page_url = None
longest_page_length = 0
subdomain_counts = {}


def process_page(url, html_content):
    global longest_page_url, longest_page_length

    # Count unique pages by URL only (fragment discarded per assignment spec)
    # Include all crawled URLs regardless of duplicate/low-word filters
    with _analytics_lock:
        if url not in unique_pages:
            unique_pages.add(url)

            netloc = urlparse(url).netloc.split(':')[0]
            if netloc in subdomain_counts:
                subdomain_counts[netloc] += 1
            else:
                subdomain_counts[netloc] = 1
                
    soup = BeautifulSoup(html_content, "lxml")
    # Remove non-visible content before text extraction
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator=" ")

    # Check for exact or near-duplicate content (skip analytics for these)
    if _duplicate_detector.is_duplicate(text):
        with _duplicates_lock:
            with open(DUPLICATES_LOG, "a", encoding="utf-8") as f:
                if f.tell() == 0:
                    f.write("url (skipped as exact or near duplicate)\n")
                f.write(f"{url}\n")
        return

    all_tokens = tokenize_text(text)
    word_count = len(all_tokens)

    # Skip longest page and word freq for low-info pages
    if word_count < MIN_WORD_COUNT:
        return

    # Filter out stopwords, single chars, 2-digit numbers, and years (1990-2099)
    tokens_filtered = [
        t for t in all_tokens
        if t not in STOP_WORDS
        and not (len(t) == 1 and t.isalnum())
        and not (len(t) == 2 and t.isdigit())
        and not (len(t) == 4 and t.isdigit() and (t.startswith("19") or t.startswith("20")))
    ]
    page_freq = computeWordFrequencies(tokens_filtered)

    with _analytics_lock:
        if word_count > longest_page_length:
            longest_page_length = word_count
            longest_page_url = url
        for word, count in page_freq.items():
            global_word_frequencies[word] = global_word_frequencies.get(word, 0) + count

def print_report():
    report_lines = []

    report_lines.append("=" * 60)
    report_lines.append("CRAWLER ANALYTICS REPORT")
    report_lines.append("=" * 60)

    report_lines.append("\n1. UNIQUE PAGES")
    report_lines.append("   Total number of distinct pages crawled. Uniqueness is by URL only, with the fragment part discarded.")
    report_lines.append(f"   {len(unique_pages)}")

    report_lines.append("\n2. LONGEST PAGE")
    report_lines.append("   The page with the highest word count (visible text only):")
    report_lines.append(f"   {longest_page_url} ({longest_page_length} words)")

    top_words = sorted(
        global_word_frequencies.items(),
        key=lambda x: x[1],
        reverse=True
    )[:50]

    report_lines.append("\n3. TOP 50 WORDS")
    report_lines.append("   Most frequent words across all pages (excluding stopwords):")
    report_lines.append("   word, count")
    for word, freq in top_words:
        report_lines.append(f"   {word} {freq}")

    report_lines.append("\n4. SUBDOMAINS AND UNIQUE PAGES")
    report_lines.append("   Number of unique pages detected in each subdomain:")
    report_lines.append("   subdomain, unique_pages")
    for subdomain in sorted(subdomain_counts.keys()):
        report_lines.append(f"   {subdomain}, {subdomain_counts[subdomain]}")

    for line in report_lines:
        print(line)
    
    with open("crawler_report.txt", "w") as f:
        for line in report_lines:
            f.write(line + "\n")
