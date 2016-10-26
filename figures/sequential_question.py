import json

from pprint import pprint
import itertools
import collections

import matplotlib.patches as pplt
import matplotlib.pyplot as plt

import numpy as np
import pandas as pd
import seaborn as sns


import re



json_file = 'guesswhat2.json'



# retrieve all the sentence
dialogues = []
with open(json_file) as f:
    for i, line in enumerate(f):
        data = json.loads(line)
        dialogues.append([d["q"] for d in data['qas']])

questions = list(itertools.chain(*dialogues))



numbers = ["first", "second", "2nd", "third", "fourth", "sixth", "seventh", "eighth" , "ninth", "tenth"]
one = ["one"]
preposition = ["his", "her", "their", "its", "him", "them"]
link = "\w \w .* it.*"


print("number of questions: " + str(len(questions)))

# # count the number of wor
# cur_counter = collections.Counter()
# cur_list = []
# for i, q in enumerate(questions):
#
#     has_one = False
#
#     if re.search(link, q):
#         cur_counter["link"] += 1
#         has_one = True
#
#     question_words = re.findall(r'\w+', re.sub('[?]', '', q))
#
#     if any(word in one for word in question_words):
#         cur_counter["one"] += 1
#         cur_list.append(2)
#         has_one = True
#
#     if any(word in numbers for word in question_words):
#         cur_counter["numbers"] += 1
#         cur_list.append(3)
#         has_one = True
#
#     if any(word in preposition for word in question_words):
#         cur_counter["preposition"] += 1
#         has_one = True
#         cur_list.append(4)
#
#
#     if has_one:
#         cur_counter["dependant"] += 1
#         cur_list.append(1)
#
# print(cur_counter)
#
# cur_counter["All"] += len(questions)
#
#
#
# sns.set(style="white")
#
# #Really really ugly hack! fail to use frequency as input! -> look df.plot(bar="")
# f = sns.distplot(np.array(cur_list), kde=False, bins=[2,3,4,5])
# f = sns.distplot(np.array(cur_list), kde=False, bins=[1,2])
# f.set_xticklabels(['', 'Total', '', "One", '', 'Numbers', '', "Preposition"], rotation=60)
#
# f.set_xlabel("Type of sequential question", {'size':'14'})
# f.set_ylabel("Number of dialogues", {'size':'14'})
#
# plt.tight_layout()
# plt.show()








def count_sequence(remaining_question, c=0):

    if len(remaining_question) == 0:
        return c

    question = remaining_question[0]
    question_words = re.findall(r'\w+', re.sub('[?]', '', question))

    if re.search(link, question) or \
        any(word in one for word in question_words) or \
        any(word in numbers for word in question_words) or \
        any(word in preposition for word in question_words):

        return count_sequence(remaining_question[1:], c+1)

    else:
        return c

seq_counter = collections.Counter()
for dialogue in dialogues:

    i = 1
    while i < len(dialogue):

        c = count_sequence(dialogue[i:])
        c = count_sequence(dialogue[i:])

        if c > 0:
            seq_counter[c] += 1
            i += c
        else:
            i += 1

print(seq_counter)


df = pd.DataFrame.from_dict(seq_counter, orient='index').reset_index()
sns.set(style="whitegrid")

f = df.get(0).plot(kind='bar', width=1, alpha = 0.3)
f.set_xlabel("Length of the sequence of questions", {'size':'14'})
f.set_ylabel("Number of sequences", {'size':'14'})



plt.show()
