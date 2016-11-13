
import json
from pprint import pprint
import itertools
import collections
import re

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import seaborn as sns


json_file = 'guesswhat.json'

status_list = []
status_count = collections.defaultdict(int)


length_list = []


with open(json_file) as f:
    for i, line in enumerate(f):

        data = json.loads(line)

        if data["status"] != "success" and data["status"] != "failure":
            data["status"] = "incomplete"

        length_list.append(len(data["qas"]))
        status_count[data["status"]] += 1
        status_list.append(data["status"])


success = np.array([s == "success" for s in status_list]) + 0
failure = np.array([s == "failure" for s in status_list]) + 0
incomp  = np.array([s == "incomplete" for s in status_list]) + 0

data = np.array([length_list, success, failure, incomp]).transpose()

sns.set_style("whitegrid", {"axes.grid": False})

df = pd.DataFrame(data, columns=['Size of Dialogues', 'Success', 'Failure', 'Incomplete'])
df = df.convert_objects(convert_numeric=True)
df = df.groupby('Size of Dialogues').sum()
df = df.div(df.sum(axis=1), axis=0)
#df = df.sort_values(by='Success')
f = df.plot(kind="bar", stacked=True, width=1, alpha=0.3)

f.set_xlim(-0.5,29.5)

plt.xlabel("Size of Dialogues", {'size':'14'})
plt.ylabel("Success ratio", {'size':'14'})

plt.tight_layout()
plt.show()
