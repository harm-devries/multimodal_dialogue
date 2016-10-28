import enchant
import json
import pickle
import string
from nltk.tokenize import WordPunctTokenizer


dialogues_file = 'guesswhat.jsonl'
correction_file = 'correction.pkl'
correction = pickle.load(open(correction_file))
correction['?'] = 0
correction[','] = 0
correction['\''] = 0
correction['/'] = 0
correction['pic'] = 'picture'
print len(correction)

d = enchant.Dict('en_US')
wpt = WordPunctTokenizer()

dictionary = {}
cnt = 0

def hasNumbers(inputString):
    return any(char.isdigit() for char in inputString)

i = 0
with open(dialogues_file) as f:
    for line in f:
        dialogue = json.loads(line)
        for qa in dialogue['qas']:
            question = qa['q'].strip()
            tokens = wpt.tokenize(qa['q'])
            new_tokens = []
            for tok in tokens:
                tok = tok.lower()
                if tok not in dictionary:
                    dictionary[tok] = True

                    if hasNumbers(tok):
                        print tok
                        i += 1
print i