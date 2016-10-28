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

number_corr = {}
number_corr['1st']  = 'first'
number_corr['1t']   = 'first'
number_corr['2nd']  = 'second'
number_corr['2d']   = 'second'
number_corr['3rd']  = 'third'
number_corr['3d']   = 'third'
number_corr['4th']  = 'fourth'
number_corr['5th']  = 'fifth'
number_corr['6th']  = 'sixth'
number_corr['7th']  = 'seventh'
number_corr['8th']  = 'eighth'
number_corr['9th']  = 'ninth'
number_corr['10th'] = 'tenth'
number_corr['11th'] = 'eleventh'
number_corr['12th'] = 'twelfth'
number_corr['13th'] = 'thirteenth'
number_corr['14th'] = 'fourteenth'
number_corr['15th'] = 'fifteenth'
number_corr['16th'] = 'sixteenth'
number_corr['17th'] = 'seventeenth'
number_corr['18th'] = 'eighteenth'

number_corr['22nd'] = 'twenty-second'
number_corr['51st'] = 'fifty-first'
number_corr['lin8e'] = 'line'
number_corr['bottl3e'] = 'bottle'
number_corr['number1'] = 'number one'
number_corr['2wheel'] = 'two wheels'
number_corr['66th'] = 'sixty-sixth'
number_corr['45mph'] = '45 miles per hour'


d = enchant.Dict('en_US')
wpt = WordPunctTokenizer()

dictionary = {}
cnt = 0

def detokenize(question, tokens, new_tokens):
    i = 0
    detok_question = ''

    for tok, new_tok in zip(tokens, new_tokens):
        if tok == question[i:i+len(tok)]:
            detok_question += new_tok
            i += len(tok)

        # do we need whitespace?
        if i < len(question) and ord(question[i]) in [32, 160]:
            detok_question += ' '
            i += 1

        # remove subsequent whitespace
        while i < len(question) and ord(question[i]) in [32, 160]:
            detok_question += ' '
            i += 1

    if detok_question[-2:] == ' ?':
        detok_question = detok_question[:-2] + '?'

    print question
    if detok_question[-1] == '/':
        detok_question = detok_question[:-1] + '?'

    if detok_question[-1] != '?':
        detok_question += '?'

    return detok_question

with open(dialogues_file) as f:
    for line in f:
        dialogue = json.loads(line)
        for qa in dialogue['qas']:
            question = qa['q'].strip()
            tokens = wpt.tokenize(qa['q'])
            new_tokens = []
            flag = False
            for tok in tokens:
                tok_lower = tok.lower()
                if tok_lower in correction and correction[tok_lower] not in ['1', '0', 0, 1]:
                    tok = correction[tok_lower]
                    if tok in number_corr:
                        tok = number_corr[tok]
                        flag = True
                    new_tokens.append(tok)
                else:
                    new_tokens.append(tok)
            print qa['id']
            print question

            detok_question = detokenize(question, tokens, new_tokens)
            if flag:
                print question
                print detok_question