

import json
from pprint import pprint
import itertools
import collections


import matplotlib.pyplot as plt

import numpy as np
import pandas as pd
import seaborn as sns


import re



import sys

if len(sys.argv) > 1:
    json_file = sys.argv[1]
else:
    json_file = 'tmp.json'


no_words = 100


# retrieve all the sentence
questions = []
with open(json_file) as f:
    for i, line in enumerate(f):
        data = json.loads(line)
        questions.append([d["q"] for d in data['qas']])
questions = list(itertools.chain(*questions))


# split questions into words
question_token = []
stopwords = ["a", "an", "is", "it", "the", "does", "do", "are", "you", "that",
             "they", "doe", "this", "there", "hi", "his", "her", "its", "picture", "can", "he", "she", "bu", "us",
             "photo"]

# count the number of wor
word_counter = collections.Counter()
for q in questions:
    q = re.sub('[?]', '', q)
    words = re.findall(r'\w+', q)
    question_token.append(words)

    for w in words:
        word_counter[w.lower()] += 1

pprint(word_counter)


stopwords=["a","an","is","it","the","does","do","are","you","that","and", "at",
           "they","doe", "this", "there", "hi", "his", "her", "its", "picture", "can", "he", "she", "bu", "us", "photo"]

print(word_counter.most_common(no_words))

for word_to_remove in stopwords:
    del word_counter[word_to_remove]

common_words = word_counter.most_common(no_words)
common_words = [pair[0] for pair in common_words]

corrmat = np.zeros((no_words,no_words))

for i, question in enumerate(question_token):

    for word in question:
        if word in common_words:

            for other_word in question:
                if other_word in common_words:
                    if word != other_word:
                        corrmat[common_words.index(word)][common_words.index(other_word)] += 1.


df = pd.DataFrame(data=corrmat, index=common_words, columns=common_words)


print(common_words)



f = sns.clustermap(df, standard_scale=0, col_cluster=False, cbar_kws={"label" : "co-occurence"})

f.ax_heatmap.xaxis.tick_top()
#f.ax_heatmap.yaxis.tick_left()

plt.setp(f.ax_heatmap.get_xticklabels(), rotation=90)
plt.setp(f.ax_heatmap.get_yticklabels(), rotation=0)

if len(sys.argv) > 1:
    from matplotlib.backends.backend_pdf import PdfPages
    pp = PdfPages('out/word_cooccurence.pdf')
    plt.savefig(pp, format='pdf')
else:
    plt.show()