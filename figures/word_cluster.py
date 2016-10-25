

import json
from pprint import pprint
import itertools
import collections


import matplotlib.pyplot as plt

import numpy as np
import seaborn as sns


import re


json_file = 'tmp.json'

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


word_counter = collections.Counter()
for q in questions:
    q = re.sub('[?]', '', q)
    words = re.findall(r'\w+', q)
    question_token.append(words)

    for w in words:
        word_counter[w.lower()] += 1

pprint(word_counter)


stopwords=["a","an","is","it","the","does","do","are","you","that",
           "they","doe", "this", "there", "hi", "his", "her", "its", "picture", "can", "he", "she", "bu", "us", "photo"]

for word_to_remove in stopwords:
    del word_counter[word_to_remove]

common_words = word_counter.most_common(20)
common_words = [pair[0] for pair in common_words]

corrmat = np.zeros((20,20))

for i, question in enumerate(question_token):

    for word in question:
        if word in common_words:

            for other_word in question:
                if other_word in common_words:
                    if word != other_word:
                        corrmat[common_words.index(word)][common_words.index(other_word)] += 1

    print(i)

print (common_words)
print corrmat

f, ax = plt.subplots(figsize=(12, 9))
sns.heatmap(corrmat, square=True)

plt.tight_layout()
plt.show()