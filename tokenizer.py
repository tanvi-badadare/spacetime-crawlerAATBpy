# from Aarabhi-edits
from collections import Counter

def tokenize_text(text):
    """
    Tokenize text into words, filtering for ASCII alphanumeric characters only.
    Returns a list of lowercase tokens.
    """
    tokens = []
    token = ''

    for character in text:
        if character.isascii() and character.isalnum():
            token += character.lower()
        else:
            if token != '':
                tokens.append(token)
                token = ''

    if token != '':
        tokens.append(token)
        
    return tokens

def computeWordFrequencies(tokens):
    """
    Compute word frequencies from a list of tokens.
    Returns a dictionary mapping words to their frequencies.
    """
    return dict(Counter(tokens))
