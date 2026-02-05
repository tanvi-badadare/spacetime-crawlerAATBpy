# from Aarabhi-edits
from tokenizer import tokenize_text, computeWordFrequencies
from bs4 import BeautifulSoup
from urllib.parse import urlparse

STOP_WORDS = {
    "a","able","about","above","abst","accordance","according","accordingly","across",
    "act","actually","added","adj","after","afterwards",
    "again","against","ah","all","almost","alone","along","already","also","although",
    "always","am","among","amongst","an","and","announce","another","any","anybody",
    "anyhow","anymore","anyone","anything","anyway","anyways","anywhere","apparently",
    "approximately","are","aren","arent","arise","around","as","aside","ask","asking",
    "at","auth","available","away","awfully","b","back","be","became","because","become",
    "becomes","becoming","been","before","beforehand","begin","beginning","beginnings",
    "begins","behind","being","believe","below","beside","besides","between","beyond",
    "biol","both","brief","briefly","but","by","c","ca","came","can","cannot","cant",
    "cause","causes","certain","certainly","co","com","come","comes","could","couldnt",
    "d","date","did","didnt","different","do","does","doesnt",
    "doing","done","dont","down","downwards","due","during","e","each","ed","edu",
    "eg","eight","eighty","either","else","elsewhere","end","ending","enough","especially",
    "et","et-al","etc","even","ever","every","everybody","everyone","everything",
    "everywhere","ex","except","f","far","few","ff","fifth","first","five","fix",
    "followed","following","follows","for","former","formerly","forth","four",
    "from","further","furthermore","g","gave","get","gets","getting","give","given",
    "gives","giving","go","goes","gone","got","gotten","h","had","happens","hardly",
    "has","hasnt","have","havent","having","he","hed","hence","her","here","hereafter",
    "hereby","herein","heres","hereupon","hers","herself","hes","hi","hid","him",
    "himself","his","hither","home","how","howbeit","however","hundred","i","id","ie",
    "if","ill","im","immediate","immediately","in","inc",
    "indeed","instead","into","inward","is","isnt",
    "it","itd","itll","its","itself","ive","j","just","k","keep","keeps","kept","kg","km",
    "know","known","knows","l","largely","last","lately","later","latter","latterly",
    "least","less","lest","let","lets","like","liked","likely","line","little","look",
    "looking","looks","ltd","m","made","mainly","make","makes","many","may","maybe","me",
    "mean","means","meantime","meanwhile","merely","mg","might","million","miss","ml",
    "more","moreover","most","mostly","mr","mrs","much","mug","must","my","myself","n",
    "na","name","namely","nay","nd","near","nearly","necessarily","necessary","need",
    "needs","neither","never","nevertheless","new","next","nine","ninety","no","nobody",
    "non","none","nonetheless","noone","nor","normally","nos","not","noted","nothing",
    "now","nowhere","o","obviously","of","off","often","oh","ok",
    "okay","old","omitted","on","once","one","ones","only","onto","or","ord","other",
    "others","otherwise","ought","our","ours","ourselves","out","outside","over","overall",
    "owing","own","p","page","pages","part","particular","particularly","past","per",
    "perhaps","placed","please","plus","poorly",
    "pp","present","previously","primarily","probably","promptly",
    "proud","put","q","que","quickly","quite","qv","r","ran","rather","rd","re",
    "readily","really","recent","recently","ref","refs","regarding","regardless","regards",
    "respectively","right","run","s","said","same","saw","say","saying","says","sec","section","see",
    "seeing","seem","seemed","seeming","seems","seen","self","selves","sent","seven",
    "several","shall","she","shed","shell","shes","should","shouldnt","show","showed",
    "shown","showns","shows",
    "since","six","slightly","so","some","somebody","somehow","someone","somethan","something",
    "sometime","sometimes","somewhat","somewhere","soon","sorry",
    "specifically","specified","specify","specifying","still","stop","strongly","sub",
    "substantially","successfully","such","sufficiently","suggest","sup","sure","t",
    "take","taken","taking","tell","tends","th","than","thank","thanks","thanx","that",
    "thatll","thats","thatve","the","their","theirs","them","themselves","then","thence",
    "there","thereafter","thereby","thered","therefore","therein","therell","thereof",
    "therere","theres","thereto","thereupon","thereve","these","they","theyd","theyll",
    "theyre","theyve","think","this","those","thou","though","thoughh","thousand","throug",
    "through","throughout","thru","thus","til","tip","to","together","too","took",
    "toward","towards","tried","tries","truly","try","trying","ts","twice","two","u","un",
    "under","unfortunately","unless","unlike","unlikely","until","unto","up","upon",
    "ups","us","usually","v","various","very","via","viz","vol","vols","vs","w","want","wants",
    "was","wasnt","way","we","wed","welcome","went","were","werent","weve",
    "what","whatever","whatll","whats","when","whence","whenever","where","whereafter",
    "whereas","whereby","wherein","wheres","whereupon","wherever","whether","which",
    "while","whim","whither","who","whod","whoever","whole","wholl","whom","whomever",
    "whos","whose","why","widely","willing","wish","with","within","without","wont",
    "words","world","would","wouldnt","www","x","y","yes","yet","you","youd","youll",
    "your","youre","yours","yourself","yourselves","youve","z","zero"
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

    soup = BeautifulSoup(html_content, "lxml")
    text = soup.get_text(separator=" ")

    # Filter stop words and single chars (a-z, A-Z, 0-9)
    tokens = [
        t for t in tokenize_text(text)
        if t not in STOP_WORDS
        and not (len(t) == 1 and t.isalnum())
    ]
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
