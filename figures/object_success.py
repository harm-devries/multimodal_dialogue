
import json
from pprint import pprint
import itertools


import matplotlib.pyplot as plt
import collections

import numpy as np
import pandas as pd
import seaborn as sns


import sys

if len(sys.argv) > 1:
    json_file = sys.argv[1]
else:
    json_file = 'guesswhat.json'

status_count = collections.Counter()
status_list = []

objects = []



with open(json_file) as f:
    for i, line in enumerate(f):

        data = json.loads(line)

        if data["status"] != "success" and data["status"] != "failure":
            data["status"] = "incomplete"

        picture = data["picture"]
        obj = data["objects"][str(data["object_id"])]

        status_count[data["status"]] += 1
        status_list.append(data["status"])

        objects.append(len(data["objects"]))



# success / failure /ration
print(status_count)



sns.set(style="whitegrid", color_codes=True)

success = np.array([s == "success" for s in status_list]) + 0
failure = np.array([s == "failure" for s in status_list]) + 0
incomp  = np.array([s == "incomplete" for s in status_list]) + 0

data = np.array([objects, success, failure, incomp]).transpose()


df = pd.DataFrame(data, columns=['No objects', 'Success', 'Failure', 'Incomplete'])
df = df.convert_objects(convert_numeric=True)
df = df.groupby('No objects').sum()
f = df.plot(kind="bar", stacked=True, width=1, alpha=0.3)

sns.regplot(x=np.array([0]), y=np.array([0]), scatter=False, line_kws={'linestyle':'--'}, label="% Success",ci=None, color="b")


f.set_xlim(0.5,18.5)
f.set_ylim(0,25000)
f.set_xlabel("Number of objects", {'size':'14'})
f.set_ylabel("Number of dialogues", {'size':'14'})
f.legend(loc="best", fontsize='large')



###########################



success = np.array([s == "success" for s in status_list])
failure = np.array([s == "failure" for s in status_list])
incomp  = np.array([s == "incomplete" for s in status_list])


sum_success    = np.array(objects)[success]
sum_failure    = np.array(objects)[np.logical_or(success, failure)]
sum_incomplete = np.array(objects)

objects = np.array(objects)
rng = range(3, 22)
histo_success = np.histogram(objects[success], bins=rng)
histo_failure = np.histogram(objects[failure], bins=rng)
histo_incomp  = np.histogram(objects[incomp], bins=rng)

print(histo_success)

normalizer = histo_success[0] + histo_failure[0] + histo_incomp[0]
histo_success = 1.0*histo_success[0] / normalizer
histo_failure = 1.0*histo_failure[0] / normalizer
histo_incomp  = 1.0*histo_incomp[0]  / normalizer


ax2 = f.twinx()

curve = np.ones(len(normalizer))-histo_failure-histo_incomp
f = sns.regplot(x=np.linspace(1, 20, 18), y=curve, order=3, scatter=False, line_kws={'linestyle':'--'},ci=None, truncate=False, color="b")
ax2.set_ylim(0,1)
ax2.grid(None)
ax2.set_ylabel("Success ratio", {'size':'14'})


plt.tight_layout()



if len(sys.argv) > 1:
    from matplotlib.backends.backend_pdf import PdfPages

    with PdfPages('out/success_objects.pdf') as pdf:
        pdf.savefig()
        plt.close()
else:
    plt.show()