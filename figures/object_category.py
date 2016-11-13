
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

categories = collections.Counter()

with open(json_file) as f:
    for i, line in enumerate(f):

        data = json.loads(line)

        object_id = data["object_id"]
        objects = data["objects"]

        object = objects[str(object_id)]
        category = object["category"]

        categories[category] += 1



c2 = categories.most_common(30)
pprint(categories)


total = 0
top = 0
for key, val in categories.items():
    total += val
for pair in c2:
    top += pair[1]

print("Cur  prop : " + str(1.0 * top/total))
print("left prop : " + str(1- 1.0*top/total))



df = pd.DataFrame([x[1] for x in c2], index=[x[0] for x in c2])
df =  df.sort_values(by=0, ascending=False)
df.columns = ['Top 30 Category']

sns.set(style="whitegrid")


f = df.plot.pie(figsize=(10, 10), subplots=True, fontsize=14)

plt.legend().set_visible(False)
plt.tight_layout()
plt.show()



