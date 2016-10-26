
import json
from pprint import pprint
import itertools


import matplotlib.pyplot as plt
import collections

import numpy as np
import seaborn as sns

import re

import sys

if len(sys.argv) > 1:
    json_file = sys.argv[1]
else:
    json_file = 'tmp.json'



dialogues = []
pictures = {}
objects = {}

ratio_q_object = []



with open(json_file) as f:
    for i, line in enumerate(f):

        data = json.loads(line)

        if data["status"] != "success" and data["status"] != "failure":
            continue

        pictures[data["picture_id"]] = 0
        objects[data["object_id"]] = 0
        dialogues.append([d["q"] for d in data['qas']])


questions = list(itertools.chain(*dialogues))

print("Number of dialogues: " + str(len(dialogues)))
print("Number of questions: " + str(len(questions)))
print("number of pictures:  " + str(len(pictures)))
print("number of objects:   " + str(len(objects)))



# Count number of questions by dialogues
q_by_d = np.zeros(len(dialogues))
for i, d in enumerate(dialogues):
    q_by_d[i] = len(d)

print("max num questions: " + str(q_by_d.max()))


# Count number of words by question
w_by_q = np.zeros(len(questions))
for i, q in enumerate(questions):
    q = re.sub('[?]', '', q)
    words = re.findall(r'\w+', q)

    w_by_q[i] = len(words)


sns.set(style="whitegrid")



#ratio question/words
f = sns.distplot(w_by_q, norm_hist =True, kde=False, bins=np.arange(3, 16, 1), color="g")

f.set_xlabel("Number of words", {'size':'14'})
f.set_ylabel("Percentage of questions", {'size':'14'})
f.set_xlim(3,14)
f.set_ylim(bottom=0)

plt.tight_layout()


if len(sys.argv) > 1:
    from matplotlib.backends.backend_pdf import PdfPages
    pp = PdfPages('out/w_q.pdf')
    plt.savefig(pp, format='pdf')
else:
    plt.show()



#ratio question/dialogues
f = sns.distplot(q_by_d, norm_hist =True, kde=False, bins=np.arange(0, 25, 1))
f.set_xlim(3,25)
f.set_ylim(bottom=0)

f.set_xlabel("Number of questions", {'size':'14'})
f.set_ylabel("Percentage of dialogues", {'size':'14'})


plt.tight_layout()



if len(sys.argv) > 1:
    from matplotlib.backends.backend_pdf import PdfPages
    pp = PdfPages('out/q_d.pdf')
    plt.savefig(pp, format='pdf')
else:
    plt.show()

