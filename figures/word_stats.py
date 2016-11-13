

import json
from pprint import pprint
import itertools
import collections
import re





json_file = 'guesswhat.test.jsonl'

words = collections.defaultdict(list)
number_words = collections.defaultdict(int)
dialogues = []

pictures = {}
objects = {}

with open(json_file) as f:
    for i, line in enumerate(f):

        data = json.loads(line)

        #if data["status"] != "success" and data["status"] != "failure": continue
        if data["status"] != "success": continue

        pictures[data["picture_id"]] = 0
        objects[data["object_id"]] = 0
        dialogues.append([d["q"] for d in data['qas']])



questions = list(itertools.chain(*dialogues))

# split questions into words
word_list = []
word_counter = collections.Counter()
for q in questions:
    q = re.sub('[?]', '', q)
    words = re.findall(r'\w+', q)

    for w in words:
        word_counter[w.lower()] += 1

size_voc = 0
size_voc_3 = 0
no_words = 0
for key, val in word_counter.items():

    no_words += val
    size_voc += 1
    if val >= 3:
        size_voc_3 += 1

print("Number of dialogues: " + str(len(dialogues)))
print("Number of questions: " + str(len(questions)))
print("number of pictures:  " + str(len(pictures)))
print("number of objects:   " + str(len(objects)))
print("Number of words:     " + str(no_words))
print("voc size:            " + str(size_voc))
print("voc size (occ >3):   " + str(size_voc_3))

