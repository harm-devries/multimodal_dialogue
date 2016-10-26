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
import sys

if len(sys.argv) > 1:
    json_file = sys.argv[1]
else:
    json_file = 'tmp.json'




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

# count the number of wor
cur_counter = collections.Counter()
cur_list = []
for i, q in enumerate(questions):

    has_one = False

    if re.search(link, q):
        cur_counter["link"] += 1
        has_one = True

    question_words = re.findall(r'\w+', re.sub('[?]', '', q))

    if any(word in one for word in question_words):
        cur_counter["one"] += 1
        has_one = True

    if any(word in numbers for word in question_words):
        cur_counter["numbers"] += 1
        has_one = True

    if any(word in preposition for word in question_words):
        cur_counter["preposition"] += 1
        has_one = True


    if has_one:
        cur_counter["All"] += 1

print(cur_counter)



sns.set(style="whitegrid")

print cur_counter
df = pd.DataFrame([x for x in cur_counter.itervalues()], index=[x for x in cur_counter])
df =  df.sort(columns=0, ascending=False)
df.columns = ['Number of questions']
f = df.plot(kind='bar', width=1, alpha = 0.3)
f.get_children()[0].set_color('g')

f.set_xticklabels(df.index, rotation=0)

f.set_xlim(-0.5,4.5)
f.set_xlabel("Type of sequential question", {'size':'14'})
f.set_ylabel("Number of questions", {'size':'14'})

plt.tight_layout()


if len(sys.argv) > 1:
    from matplotlib.backends.backend_pdf import PdfPages

    with PdfPages('out/seq_question_total.pdf') as pdf:
        pdf.savefig()
        plt.close()
else:
    plt.show()




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


df = pd.DataFrame([x for x in seq_counter.itervalues()], index=[x for x in seq_counter])
df =  df.sort(columns=0, ascending=False)
df.columns = ['Number of questions']

sns.set(style="whitegrid")

f = df.plot(kind='bar', width=1, alpha = 0.3)
f.set_xlabel("Length of the sequence of questions", {'size':'14'})
f.set_ylabel("Number of sequences", {'size':'14'})
f.set_xticklabels(df.index, rotation=0)
f.set_xlim(-0.5,6.5)
f.set_ylim(bottom=0)

plt.tight_layout()

if len(sys.argv) > 1:
    from matplotlib.backends.backend_pdf import PdfPages

    with PdfPages('out/seq_question_length.pdf') as pdf:
        pdf.savefig()
        plt.close()
else:
    plt.show()