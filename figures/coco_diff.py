import json

import psycopg2
from pprint import pprint

import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import collections


training_file = '/home/fstrub/Downloads/annotations/instances_train2014.json'
validation_file = '/home/fstrub/Downloads/annotations/instances_val2014.json'

min_area = 50
min_object = 3
max_object = 20

area_coco = []
category_coco = []

print("loading training file...")
with open(training_file) as data_file:
    data = json.load(data_file)

    categories = {}
    for c in data["categories"]:
        categories[int(c["id"])] = c["name"]

    for obj in data["annotations"]:
        area_coco.append(float(obj["area"]))
        category_coco.append(categories[int(obj["category_id"])])

print("loading validation file...")
with open(validation_file) as data_file:
    data = json.load(data_file)
    for obj in data["annotations"]:
        area_coco.append(float(obj["area"]))
        category_coco.append(categories[int(obj["category_id"])])

#remove outliers
area_coco = [area for area in area_coco if area > 0]

print("loading the guesswhat db...")
conn = psycopg2.connect('')
cur = conn.cursor()

cur.execute('SELECT area, "name" FROM object o, object_category oc WHERE o.category_id = oc.category_id')

area_gw = []
category_gw = []
for row in cur.fetchall():
    area_gw.append(float(row[0]))
    category_gw.append(row[1])


# area_hist_coco = np.histogram(np.log(area_coco), bins=np.linspace(2, 15, 12))
# area_hist_gw   = np.histogram(np.log(area_gw)  , bins=np.linspace(2, 15, 12))
#
# area = np.array([area_hist_gw[0], area_hist_coco[0]]).transpose()
# sns.set(style="whitegrid")
#
# df = pd.DataFrame(area, columns=['GuessWhat', 'Coco'])
# df["Coco"] -= df["GuessWhat"]
# df.plot(kind="bar", width=1, alpha=0.3, stacked=True)
#
# plt.tight_layout()
# plt.show()


category_serie_coco = pd.Series(category_coco).astype('str').value_counts()
category_serie_gw = pd.Series(category_gw).astype('str').value_counts()

df = pd.concat([category_serie_gw,category_serie_coco], axis=1)
df.columns = ['GuessWhat', 'Coco']
df = df.sort_values(by='Coco', ascending=False)
df["Coco"] -= df["GuessWhat"]
print(df.ix['person'])
#df = df.drop(["person"])
f = df.plot(kind="bar", width=1, alpha=0.3, stacked=True, figsize=(14,6))
f.set_xlim(left=-0.5)

plt.tight_layout()
plt.show()