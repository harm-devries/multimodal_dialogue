
import json
from pprint import pprint
import itertools


import matplotlib.pyplot as plt
import collections

import numpy as np
import seaborn as sns


json_file = 'guesswhat2.json'


status = []
status_list = collections.defaultdict(list)

center = []
status_count = collections.defaultdict(int)

x_bin = 7
y_bin = 7

def get_center(bbox, picture):
    width = picture["width"]
    height = picture["height"]

    x_up  = 1.0 * bbox[0]
    y_up  = 1.0 * bbox[1]
    x_down = x_up + bbox[2]
    y_down = y_up + bbox[3]


    x_center = (x_up + x_down) / ( 2. * width)
    y_center = (y_up + y_down) / ( 2. * height)

    return [x_center, y_center]



with open(json_file) as f:
    for i, line in enumerate(f):

        data = json.loads(line)

        picture = data["picture"]
        obj = data["objects"][str(data["object_id"])]

        status.append(data["status"])
        center.append(get_center( obj["bbox"],picture))



success_sum = np.zeros((x_bin+1, y_bin+1))
total_sum = np.zeros((x_bin+1, y_bin+1))

for pos, s in zip(center, status):

    x = int(pos[0] * x_bin)
    y = int(pos[1] * y_bin)

    total_sum[x][y] += 1.0

    if s == "success":
        success_sum[x][y] += 1.0

ratio = 1.0 * success_sum / total_sum


sns.set(style="whitegrid")


# Draw the heatmap with the mask and correct aspect ratio
f = sns.heatmap(ratio, robust=True, linewidths=.5)
f.set_xlabel("normalized x-axis", {'size':'14'})
f.set_ylabel("normalized y-axis", {'size':'14'})

plt.tight_layout()
plt.show()