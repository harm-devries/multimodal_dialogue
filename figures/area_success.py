
import json
from pprint import pprint
import itertools


import matplotlib.pyplot as plt
import collections

import pandas as pd
import numpy as np
import seaborn as sns
import sys


if len(sys.argv) > 1:
    json_file = sys.argv[1]
else:
    json_file = 'guesswhat.json'


status = []
status_list = collections.defaultdict(list)

area_list = []
status_count = collections.defaultdict(int)



with open(json_file) as f:
    for i, line in enumerate(f):

        data = json.loads(line)

        if data["status"] != "success" and data["status"] != "failure":
            data["status"] = "incomplete"

        picture = data["picture"]
        obj = data["objects"][str(data["object_id"])]

        status_count[data["status"]] += 1
        status.append(data["status"])

        area_list.append(float(obj["area"]))


# success / failure /ration
print(status_count)

success = np.array([s == "success" for s in status])
failure = np.array([s == "failure" for s in status])
incomp  = np.array([s == "incomplete" for s in status])

data = np.array([np.log(area_list), success, failure, incomp]).transpose()

sns.set(style="whitegrid", color_codes=True)

rng = range(4, 13)

df = pd.DataFrame(data, columns=['Area', 'Success', 'Failure', 'Incomplete'])
df = df.convert_objects(convert_numeric=True)
df = df.groupby(pd.cut(df["Area"], range(4,14))).sum()
df = df.drop('Area', 1)
f = df.plot(kind="bar", stacked=True, width=1, alpha=0.3, figsize=(9,6))

f.set_xlim(-0.5,8.5)
f.set_ylim(0,30000)
f.set_xlabel("log of object area", {'size':'14'})
f.set_ylabel("Number of dialogues", {'size':'14'})


sns.regplot(x=np.array([0]), y=np.array([0]), scatter=False, line_kws={'linestyle':'--'}, label="% Success",ci=None, color="b")

f.legend(loc="upper left", fontsize='x-large')

#df.groupby(pd.cut(df["B"], np.arange(0, 1.0+0.155, 0.155))).sum()






sum_success    = np.array(area_list)[success]
sum_failure    = np.array(area_list)[np.logical_or(success, failure)]
sum_incomplete = np.array(area_list)

histo_success = np.histogram(np.log(area_list)[success], bins=rng)
histo_failure = np.histogram(np.log(area_list)[failure], bins=rng)
histo_incomp  = np.histogram(np.log(area_list)[incomp] , bins=rng)

normalizer = histo_success[0] + histo_failure[0] + histo_incomp[0]
histo_success = 1.0*histo_success[0] / normalizer
histo_failure = 1.0*histo_failure[0] / normalizer
histo_incomp  = 1.0*histo_incomp[0]  / normalizer




ax2 = f.twinx()

curve = np.ones(len(normalizer))-histo_failure-histo_incomp
f = sns.regplot(x=np.linspace(1, 10, 8), y=curve, order=3, scatter=False, line_kws={'linestyle':'--'},ci=None, truncate=False, color="b")
ax2.set_ylim(0,1)
ax2.grid(None)
ax2.set_ylabel("Success ratio", {'size':'14'})


plt.tight_layout()


if len(sys.argv) > 1:
    from matplotlib.backends.backend_pdf import PdfPages

    with PdfPages('out/success_area.pdf') as pdf:
        pdf.savefig()
        plt.close()
else:
    plt.show()
