
import json
from pprint import pprint
import itertools

import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import collections

import re


json_file = 'tmp.json'



qas = []
dialogues = []
pictures = {}
objects = {}

with open(json_file) as f:
    for i, line in enumerate(f):
        data = json.loads(line)
        pictures[data["picture_id"]] = 0
        objects[data["object_id"]] = 0
        qas.append(data['qas'])
        dialogues.append([d["q"] for d in data['qas']])


questions = list(itertools.chain(*dialogues))

print("Number of dialogues: " + str(len(dialogues)))
print("Number of questions: " + str(len(questions)))
print("number of pictures:  " + str(len(objects)))
print("number of objects:   " + str(len(pictures)))


sns.set(style="white", palette="muted", color_codes=True)


# Count number of questions by dialogues
q_by_d = np.zeros(len(dialogues))
for i, d in enumerate(dialogues):
    q_by_d[i] = len(d)

print("max num questions: " + str(q_by_d.max()))


# Count number of words by question
w_by_q = np.zeros(len(questions))
word_counter = collections.Counter()
for i, q in enumerate(questions):
    q = re.sub('[?]', '', q)
    words = re.findall(r'\w+', q)

    w_by_q[i] = len(words)

    for w in words:
        word_counter[w.lower()] += 1


pprint(word_counter)





# Set up the matplotlib figure
f, axes = plt.subplots(1,2 , figsize=(7, 7))


sns.despine(left=True)
sns.distplot(q_by_d, norm_hist =True, kde=False, bins=np.arange(0.5, 25.5, 1), ax=axes[0], axlabel="Number of questions by dialogues")
sns.distplot(w_by_q, norm_hist =True, kde=False, bins=np.arange(2.5, 15.5, 1), ax=axes[1], color="g", axlabel="Number of words by questions")

f.tight_layout()


plt.show()