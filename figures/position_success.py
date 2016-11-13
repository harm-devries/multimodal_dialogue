
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

status = []
status_list = collections.defaultdict(list)

center = []
status_count = collections.defaultdict(int)

x_bin = 7
y_bin = 7

def get_center(bbox, picture):
    im_width = picture["width"]
    im_height = picture["height"]

    x_width = bbox[2]
    y_height = bbox[3]

    x_left = bbox[0]
    y_upper = im_height - bbox[1]


    x_center = (x_left + 0.5 * x_width) / im_width
    y_center = (y_upper - 0.5 * y_height)/ im_height

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
f = sns.heatmap(ratio, robust=True, linewidths=.5, cbar_kws={"label" : "% Success"}, xticklabels=False, yticklabels=False)
f.set_xlabel("normalized image width", {'size':'14'})
f.set_ylabel("normalized image height", {'size':'14'})
f.legend(loc="upper left", fontsize='x-large')
plt.tight_layout()



if len(sys.argv) > 1:
    from matplotlib.backends.backend_pdf import PdfPages

    with PdfPages('out/success_spatial.pdf') as pdf:
        pdf.savefig()
        plt.close()
else:
    plt.show()