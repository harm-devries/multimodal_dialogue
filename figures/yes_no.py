
import json
from pprint import pprint
import itertools


import matplotlib.pyplot as plt
import collections

import numpy as np
import seaborn as sns

import re



json_file = 'guesswhat2.json'
json_file = 'tmp.json'



yes_no = []

number_yesno = {"yes" : 0, "no": 0, "NA" : 0}


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


        x = np.linspace(0,1,len(yn))
        yes_no.append(np.array([x,yn]))




yes_no = np.concatenate([ys for ys in yes_no], axis=1).transpose()

print(number_yesno)



sns.set(style="whitegrid")


f = sns.regplot(x=yes_no[:,0], y=yes_no[:,1], x_bins=10, order=3, label="Yes-no ratio", marker=".", truncate=True)

f.set_xlim(0,1)
f.set_ylim(0,1)
f.set_xlabel("ratio yes-no")
f.set_ylabel('Dialogue advancement')

plt.tight_layout()
plt.show()



