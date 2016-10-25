
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

area = []
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

        area.append(float(obj["area"]))


# success / failure /ration
print(status_count)

success = np.array([s == "success" for s in status])
failure = np.array([s == "failure" for s in status])
incomp  = np.array([s == "incomplete" for s in status])


sns.set(style="whitegrid", color_codes=True)



rng = range(4, 13)


sum_success    = np.array(area)[success]
sum_failure    = np.array(area)[np.logical_or(success, failure)]
sum_incomplete = np.array(area)


sns.distplot(np.log(sum_incomplete)  , bins=rng, kde=False, label="Incomplete", color="g")
sns.distplot(np.log(sum_failure)     , bins=rng, kde=False, label="Failure"   , color="r")
f =  sns.distplot(np.log(sum_success), bins=rng, kde=False, label="Success"   , color="b")

#Dummy legend
sns.regplot(x=np.array([-1]), y=np.array([-1]), scatter=False, line_kws={'linestyle':'--'}, label="% Success",ci=None, color="b")


histo_success = np.histogram(np.log(area)[success], bins=rng)
histo_failure = np.histogram(np.log(area)[failure], bins=rng)
histo_incomp  = np.histogram(np.log(area)[incomp] , bins=rng)

normalizer = histo_success[0] + histo_failure[0] + histo_incomp[0]
histo_success = 1.0*histo_success[0] / normalizer
histo_failure = 1.0*histo_failure[0] / normalizer
histo_incomp  = 1.0*histo_incomp[0]  / normalizer


f.set_xlim(4,12)
f.set_xlabel("log10 of the area", {'size':'14'})
f.set_ylabel("Number of dialogues", {'size':'14'})
f.legend(loc="upper left", fontsize='large')

ax2 = f.twinx()

curve = np.ones(len(normalizer))-histo_failure-histo_incomp
f = sns.regplot(x=np.linspace(4, 13, 8), y=curve, order=3, scatter=False, line_kws={'linestyle':'--'},ci=None, truncate=False, color="b")
ax2.set_xlim(4,12)
ax2.set_ylim(0,1)
ax2.grid(None)
ax2.set_ylabel("Success ratio", {'size':'14'})


plt.tight_layout()
plt.show()