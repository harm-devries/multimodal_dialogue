import json
from pprint import pprint
import itertools


import matplotlib.pyplot as plt
import collections

import numpy as np
import seaborn as sns

import re


json_file = 'guesswhat.json'

ratio_q_object = []


with open(json_file) as f:
    for i, line in enumerate(f):

        data = json.loads(line)

        if data["status"] != "success" and data["status"] != "failure":
            continue

        no_object = len(data['objects'])
        no_question = len(data['qas'])

        ratio_q_object.append([no_object,no_question])


ratio_q_object = np.array(ratio_q_object)


sns.set(style="whitegrid")



x = np.linspace(3, 20, 80)
sns.regplot    (x=ratio_q_object[:,0], y=ratio_q_object[:,1], x_bins=17, order=4, label="Human behavior", marker=".")

sns.regplot    (x=x, y=np.log2(x), order=6, scatter=False, label="y = log2(x)", line_kws={'linestyle':'--'})
f = sns.regplot(x=x, y=x         , order=1, scatter=False, label="y = x"      , line_kws={'linestyle':'--'})

f.legend(loc="best")
f.set_xlim(3,20)
f.set_ylim(0,20)
f.set_xlabel("Number of objects", {'size':'14'})
f.set_ylabel("Number of questions", {'size':'14'})

plt.tight_layout()
plt.show()






