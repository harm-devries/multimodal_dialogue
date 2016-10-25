
import json
from pprint import pprint
import itertools


import matplotlib.pyplot as plt
import collections

import numpy as np
import seaborn as sns


json_file = 'guesswhat.json'


status = []
status_list = collections.defaultdict(list)

objects = []
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

        objects.append(len(data["objects"]))



# success / failure /ration
print(status_count)

success = np.array([s == "success" for s in status])
failure = np.array([s == "failure" for s in status])
incomp  = np.array([s == "incomplete" for s in status])

objects = np.array(objects)

sns.set(style="white", color_codes=True)



rng = range(3, 22)


sum_success    = np.array(objects)[success]
sum_failure    = np.array(objects)[np.logical_or(success, failure)]
sum_incomplete = np.array(objects)


sns.distplot(sum_incomplete  , bins=rng, kde=False, label="Incomplete", color="g")
sns.distplot(sum_failure     , bins=rng, kde=False, label="Failure"   , color="r")
f =  sns.distplot(sum_success, bins=rng, kde=False, label="Success"   , color="b")

#Dummy legend
sns.regplot(x=np.array([-1]), y=np.array([-1]), scatter=False, line_kws={'linestyle':'--'}, label="% Success",ci=None, color="grey")

histo_success = np.histogram(objects[success], bins=rng)
histo_failure = np.histogram(objects[failure], bins=rng)
histo_incomp  = np.histogram(objects[incomp], bins=rng)

print(histo_success)

normalizer = histo_success[0] + histo_failure[0] + histo_incomp[0]
histo_success = 1.0*histo_success[0] / normalizer
histo_failure = 1.0*histo_failure[0] / normalizer
histo_incomp  = 1.0*histo_incomp[0]  / normalizer


f.set_xlim(3,20)
f.set_ylim(bottom=0)
f.set_xlabel("Number of objects", {'size':'14'})
f.set_ylabel("Number of dialogues", {'size':'14'})
f.legend(loc="best", fontsize='large')

ax2 = f.twinx()

curve = np.ones(len(normalizer))-histo_failure-histo_incomp
f = sns.regplot(x=np.linspace(3, 22, 18), y=curve, order=3, scatter=False, line_kws={'linestyle':'--'},ci=None, truncate=False, color="grey")
ax2.set_xlim(3,20)
ax2.set_ylim(0,1)
ax2.grid(None)
ax2.set_ylabel("Success ratio", {'size':'14'})


plt.tight_layout()
plt.show()