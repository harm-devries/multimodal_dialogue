import io
import json
import numpy

# from gensim.models import Word2Vec
from nltk.tokenize import WordPunctTokenizer

use_word_embeddings = False
min_nr_of_occurrences = 3
out_file = 'dict.json'
dialogues_file = '/Users/harmdevries/Documents/multimodal_dialogue/data/guesswhat.train.jsonl'
wpt = WordPunctTokenizer()

if use_word_embeddings:
    word2vec = Word2Vec.load_word2vec_format('/Users/hdevries/Downloads/GoogleNews-vectors-negative300.bin.gz', binary=True)

word2i = {'<unk>': 1,
          '<start>': 2,
          '<stop>': 3,
          '<padding>': 4}

word2emb = {'<unk>': numpy.zeros((300,)).tolist(), 
            '<start>': numpy.zeros((300,)).tolist(), 
            '<stop>': numpy.zeros((300,)).tolist(), 
            '<padding>': numpy.zeros((300,)).tolist()}
i = 5

word2occ = {}

k = 0
with open(dialogues_file) as f:
    for line in f:
        k += 1
        dialogue = json.loads(line)

        for qa in dialogue['qas']:
            tokens = wpt.tokenize(qa['q'])
            for tok in tokens:
                tok = tok.lower()
                if tok in word2occ:
                    word2occ[tok] += 1
                else:
                    word2occ[tok] = 1
print k
print len(word2occ)

included_cnt = 0
excluded_cnt = 0
for word, occ in word2occ.iteritems():

    if occ >= min_nr_of_occurrences:
        included_cnt += occ
        word2i[word] = i
        if use_word_embeddings and word in word2vec:
            word2emb[word] = word2vec[word]
        i += 1
    else:
        excluded_cnt += occ

print included_cnt
print excluded_cnt

print len(word2i)

with io.open(out_file, 'w', encoding='utf8') as f_out:
    data = json.dumps({'word2i': word2i, 'word2emb': word2emb}, ensure_ascii=False)
    f_out.write(unicode(data))