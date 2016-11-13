
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
    json_file = 'guesswhat.json'



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



sns.set_style("whitegrid", {"axes.grid": False})



#ratio question/words
f = sns.distplot(w_by_q, norm_hist =True, kde=False, bins=np.arange(2.5, 15.5, 1), color="g")

f.set_xlabel("Number of words", {'size':'14'})
f.set_ylabel("Ratio of questions", {'size':'14'})
f.set_xlim(2.5,14.5)
f.set_ylim(bottom=0)

plt.tight_layout()


if len(sys.argv) > 1:
    from matplotlib.backends.backend_pdf import PdfPages

    with PdfPages('out/w_q.pdf') as pdf:
        pdf.savefig()
        plt.close()
else:
    plt.show()


sns.set_style("whitegrid", {"axes.grid": False})


#ratio question/dialogues
f = sns.distplot(q_by_d, norm_hist =True, kde=False, bins=np.arange(0.5, 25.5, 1))
f.set_xlim(0.5,25.5)
f.set_ylim(bottom=0)

f.set_xlabel("Number of questions", {'size':'14'})
f.set_ylabel("Ratio of dialogues", {'size':'14'})

#hist= np.histogram(q_by_d, bins=np.arange(0, 25, 1), density=True)
#sns.regplot(x=hist[1][3:-1], y=np.log(hist[0][3:]))

plt.tight_layout()



if len(sys.argv) > 1:
    from matplotlib.backends.backend_pdf import PdfPages

    with PdfPages('out/q_d.pdf') as pdf:
        pdf.savefig()
        plt.close()
else:
    plt.show()




