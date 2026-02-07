from collections import Counter

def tokenize_text(text):
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
    return dict(Counter(tokens))
