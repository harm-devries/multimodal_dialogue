import json
from pprint import pprint
import collections
import logging
import sys
import numpy as np
import re

from gensim import corpora, models, similarities

import seaborn as sns
import matplotlib.pyplot as plt

from gensim.models.wrappers.dtmmodel import DtmModel


### WARNING : one must first compile and install https://github.com/magsilva/dtm/tree/master/bin

path_to_dtm = 'dtm/dtm/main'

if len(sys.argv) > 1:
    json_file = sys.argv[1]
else:
    json_file = 'guesswhat.json'


stopwords = ["a", "an", "is", "it", "the", "does", "do", "are", "you", "that", "and",
                 "they", "doe", "this", "there", "hi", "his", "her", "its", "can", "he", "she", "us", "?", "for"]


#Retrieve the dialogues
dialogues = collections.defaultdict(list)
with open(json_file) as f:
    for i, line in enumerate(f):

        data = json.loads(line)

        # Focus on sucessful dialogues
        if data["status"] != "success":
            continue

        # Focus on dialogues of size 6
        if len(data['qas']) != 6:
            continue

        for i, d in enumerate(data['qas']):
            dialogues[i] += [re.sub('[?]', '', word) for word in d["q"].lower().split() if word not in stopwords and len(word) > 2]


dialogues = [x for x in dialogues.values()]


no_topics = 2
#Create class wrapper
class DTMcorpus(corpora.textcorpus.TextCorpus):
    def get_texts(self):
        return self.input

    def __len__(self):
        return len(self.input)
corpus = DTMcorpus(dialogues)


logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
model = DtmModel(path_to_dtm, corpus, time_slices=[1,1,1,1,1,1], num_topics=no_topics,id2word=corpus.dictionary, initialize_lda=True)


for i in range(0, no_topics):
    print(model.show_topic(topicid=i, time=0, num_words=8))


m = np.array(model.gamma_)

sns.set(style="whitegrid")
f, ax = plt.subplots()
for j in range(0, no_topics):
    plt.plot(np.arange(1, 7, 1), m[:, j], '-o', label="Topic {}".format(j))

f.legend(*ax.get_legend_handles_labels(), loc="center right",  fontsize='x-large')

ax.set_xlabel("Dialogue length", {'size': '16'})
ax.set_ylabel('Proportion of topics', {'size': '16'})

plt.tight_layout()
plt.show()