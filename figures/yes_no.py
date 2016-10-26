
import json
from pprint import pprint
import itertools


import matplotlib.pyplot as plt
import collections

import numpy as np
import seaborn as sns


import sys

if len(sys.argv) > 1:
    json_file = sys.argv[1]
else:
    json_file = 'tmp.json'




yes_no = collections.defaultdict(list)
number_yesno = collections.defaultdict(int)


with open(json_file) as f:
    for i, line in enumerate(f):

        data = json.loads(line)

        if data["status"] != "success" and data["status"] != "failure":
            continue

        yn = []
        for _qas in data['qas']:
            answer = _qas["a"]

            if answer == "Yes":
                number_yesno["yes"] +=1
                yn.append(1)
            elif answer == "No":
                number_yesno["no"] += 1
                yn.append(0)
            else:
                number_yesno["NA"] += 1
                yn.append(0.5)

        no_question = len(data["qas"])
        yes_no[no_question].append(yn)

print(number_yesno)



sns.set(style="whitegrid")

for key, yn in yes_no.items():

    no_question = int(key)
    yn_mean = np.array(yn).mean(axis=0)

    if no_question < 15 :
        f = sns.regplot(x=np.arange(1, no_question + 1, 1), y=yn_mean, lowess=True, scatter=False)

#dummy legend
sns.regplot(x=np.array([-1]), y=np.array([-1]), scatter=False, line_kws={'linestyle':'-'}, label="Ratio yes-no",ci=None, color="g")
f.legend(loc="best", fontsize='large')

f.set_xlim(1,14)
f.set_ylim(0.1,1)
f.set_xlabel("Number of questions", {'size':'14'})
f.set_ylabel('Ratio yes-no', {'size':'14'})

plt.tight_layout()



if len(sys.argv) > 1:
    from matplotlib.backends.backend_pdf import PdfPages
    pp = PdfPages('out/yes_no.pdf')
    plt.savefig(pp, format='pdf')
else:
    plt.show()


