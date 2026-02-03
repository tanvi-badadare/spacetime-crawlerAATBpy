# from Aarabhi-edits
from tokenizer import tokenize_text, computeWordFrequencies
from bs4 import BeautifulSoup
from urllib.parse import urlparse

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
    "without","would","yet","you","your","yours","yourself","yourselves"
}


unique_pages = set()
global_word_frequencies = {}
longest_page_url = None
longest_page_length = 0
subdomain_counts = {}

def process_page(url, html_content):
    """
    Process a page for analytics: extract text, tokenize, count words, track subdomains.
    """
    global longest_page_url, longest_page_length

    unique_pages.add(url)

    netloc = urlparse(url).netloc.split(':')[0]
    if netloc in subdomain_counts:
        subdomain_counts[netloc] += 1
    else:
        subdomain_counts[netloc] = 1

    soup = BeautifulSoup(html_content, "html.parser")
    text = soup.get_text(separator=" ")

    tokens = [t for t in tokenize_text(text) if t not in STOP_WORDS]
    word_count = len(tokens)

    if word_count > longest_page_length:
        longest_page_length = word_count
        longest_page_url = url

    page_freq = computeWordFrequencies(tokens)
    for word, count in page_freq.items():
        global_word_frequencies[word] = global_word_frequencies.get(word, 0) + count

def print_report():
    """
    Print analytics report to console and save to crawler_report.txt file.
    """
    report_lines = []

    report_lines.append(f"Unique pages: {len(unique_pages)}")
    report_lines.append(f"Longest page: {longest_page_url} ({longest_page_length} words)")

    # Fixed: changed keys=lambda to key=lambda
    top_words = sorted(
        global_word_frequencies.items(),
        key=lambda x: x[1],
        reverse=True
    )[:50]
    
    report_lines.append("\nTop 50 words:")
    for word, freq in top_words:
        report_lines.append(f"{word} {freq}")

    report_lines.append("\nSubdomain counts:")
    for subdomain in sorted(subdomain_counts.keys()):
        report_lines.append(f"{subdomain}, {subdomain_counts[subdomain]}")

    for line in report_lines:
        print(line)
    
    with open("crawler_report.txt", "w") as f:
        for line in report_lines:
            f.write(line + "\n")
