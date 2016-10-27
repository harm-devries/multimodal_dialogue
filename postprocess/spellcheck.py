import enchant
import json
import operator
import os.path
import pickle
import readline
from itertools import islice
from nltk.tokenize import WordPunctTokenizer


dict_file = 'dictionary.pkl'
correction_file = 'correction.pkl'
dialogues_file = '/Users/hdevries/Downloads/dialogues(2).txt'
wpt = WordPunctTokenizer()

d = enchant.Dict('en_US')
in_dict = {}
not_in_dict = {}

if os.path.isfile(dict_file):
    di = pickle.load(open(dict_file, 'rb'))
    in_dict = di['in_dict']
    not_in_dict = di['not_in_dict']
else:
    with open(dialogues_file) as f, open(dict_file, 'wb') as out_f:
        for line in f:
            dialogue = json.loads(line)
            for qa in dialogue['qas']:
                tokens = wpt.tokenize(qa['q'])
                for tok in tokens:
                    tok = tok.lower()
                    if d.check(tok):
                        if tok in in_dict:
                            in_dict[tok] += 1
                        else:
                            in_dict[tok] = 1
                    else:
                        if tok in not_in_dict:
                            not_in_dict[tok].append(qa['q'])
                        else:
                            not_in_dict[tok] = [qa['q']]
        pickle.dump({'in_dict': in_dict, 'not_in_dict': not_in_dict}, out_f)

def take(n, iterable):
    return list(islice(iterable, n))

if os.path.isfile(correction_file):
    correction = pickle.load(open(correction_file))
else:
    correction = {}

def rlinput(prompt, prefill=''):
   readline.set_startup_hook(lambda: readline.insert_text(prefill))
   try:
      return raw_input(prompt)
   finally:
      readline.set_startup_hook()

not_in_dict_counts = {}
for k, v in not_in_dict.iteritems():
    not_in_dict_counts[k] = len(v)

sorted_not_in_dict = sorted(not_in_dict_counts.items(), key=operator.itemgetter(1), reverse=True)

# Some manual corrections
correction['fron'] = '1'
correction['wearng'] = 'wearing'
correction["/.'"] = '?'

print type(sorted_not_in_dict)
cnt = sum([1 for k, v in sorted_not_in_dict if v >= 3])
print cnt
print len(correction)
cnt2 = 0
for k, c in sorted_not_in_dict:
    if k not in correction:
        print cnt2
        v = not_in_dict[k]
        print v
        all_sug = [(s, s in in_dict) for s in d.suggest(k)[:5]]
        print all_sug
        try:
            sug = next(s[0] for s in all_sug if s[1])  # pick first suggestion that is in the dictionary
        except StopIteration:
            if len(all_sug) > 0:
                sug = all_sug[0][0]  # take first suggestion
            else: 
                sug = None
        print k
        print "0 for no correction"
        print "1 for per case correction"
        corr = rlinput('Correction: ', prefill=sug)
        correction[k] = corr
        f_out = open(correction_file, 'wb')
        pickle.dump(correction, f_out)
        f_out.close()
    else:
        cnt2 += c
