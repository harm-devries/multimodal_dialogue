
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


category_list = []
category_count = collections.Counter()


with open(json_file) as f:
    for i, line in enumerate(f):

        data = json.loads(line)

        if data["status"] != "success" and data["status"] != "failure":
            data["status"] = "incomplete"

        object_id = data["object_id"]
        objects = data["objects"]

        object = objects[str(object_id)]
        category = object["category"]

        category_count[category] += 1
        category_list.append(category)

        status_count[data["status"]] += 1
        status_list.append(data["status"])




c2 = category_count.most_common(30)



success = np.array([s == "success" for s in status_list]) + 0
failure = np.array([s == "failure" for s in status_list]) + 0
incomp  = np.array([s == "incomplete" for s in status_list]) + 0

data = np.array([category_list, success, failure, incomp]).transpose()

sns.set(style="white", color_codes=True)


df = pd.DataFrame(data, columns=['Category', 'Success', 'Failure', 'Incomplete'])
df = df.convert_objects(convert_numeric=True)
df = df.groupby('Category').sum()
df = df.div(df.sum(axis=1), axis=0)
df = df.sort_values(by='Success')
df.plot(kind="bar", stacked=True, width=1, alpha=0.3, figsize=(14,6))
sns.set(style="whitegrid")

plt.xlabel("Categories", {'size':'14'})
plt.ylabel("Success ratio", {'size':'14'})

plt.tight_layout()
plt.show()



