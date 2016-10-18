
import json
from pprint import pprint
import itertools

import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import collections

from wordcloud import WordCloud

import re


json_file = 'tmp.json'



qas = []
dialogues = []
pictures = {}
objects = {}

with open(json_file) as f:
    for i, line in enumerate(f):
        data = json.loads(line)
        pictures[data["picture_id"]] = 0
        objects[data["object_id"]] = 0
        qas.append(data['qas'])
        dialogues.append([d["q"] for d in data['qas']])


questions = list(itertools.chain(*dialogues))

print("Number of dialogues: " + str(len(dialogues)))
print("Number of questions: " + str(len(questions)))
print("number of pictures:  " + str(len(objects)))
print("number of objects:   " + str(len(pictures)))


sns.set(style="white", palette="muted", color_codes=True)


# Count number of questions by dialogues
q_by_d = np.zeros(len(dialogues))
for i, d in enumerate(dialogues):
    q_by_d[i] = len(d)

print("max num questions: " + str(q_by_d.max()))


# Count number of words by question
w_by_q = np.zeros(len(questions))
word_counter = collections.Counter()
word_list = []
for i, q in enumerate(questions):
    q = re.sub('[?]', '', q)
    words = re.findall(r'\w+', q)

    w_by_q[i] = len(words)
    word_list.append(words)

    for w in words:
        word_counter[w.lower()] += 1


word_list = list(itertools.chain(*word_list))

pprint(word_counter)





# Set up the matplotlib figure
f, axes = plt.subplots(1,2 , figsize=(7, 7))


sns.despine(left=True)
sns.distplot(q_by_d, norm_hist =True, kde=False, bins=np.arange(0.5, 25.5, 1), ax=axes[0], axlabel="Number of questions by dialogues")
sns.distplot(w_by_q, norm_hist =True, kde=False, bins=np.arange(2.5, 15.5, 1), ax=axes[1], color="g", axlabel="Number of words by questions")

f.tight_layout()


plt.show()


def color_func(word=None, font_size=None, position=None,  orientation=None, font_path=None, random_state=None):
    color_list =["green",'blue', 'brown', "red", 'white', "black", "yellow", "color", "orange"]
    people_list  =['people', 'person', "he", "she", "human"]
    prep = ['on', "in", 'of', 'to', "with"]
    number = ['one', "two", "three", "four", "five", "six"]
    spatial = ["left", "right", "side", "next", "front", "middle", "background", "near", "behind"]
    verb=["wearing", "have", "can", "holding", "sitting"]
    misc = ["picture"]
    obj = ["table", 'car', "food", 'animal', "shirt", "something", ""]

    if word in color_list: return 'rgb(0, 102, 204)' #blue
    if word in people_list: return  'rgb(255, 0, 0)' #red
    if word in prep: return 'rgb(0, 153, 0)' #green
    if word in number: return 'rgb(204, 204, 0)' #yellow
    if word in spatial: return 'rgb(204, 102, 0)' #purple
    if word in verb: return 'rgb(0, 204, 102)' #turquoise
    if word in obj: return 'rgb(64, 64, 64)' #grey
    else:
        return 'rgb(255, 128, 0)' #orange

stopwords=["a","an","is","it","the","does","do","are","you","that","they","doe"]

# take relative word frequencies into account, lower max_font_size
wordcloud = WordCloud(background_color="white", color_func=color_func, max_font_size=30, max_words=100, stopwords=stopwords )\
    .generate(" ".join(str(x) for x in word_list))
plt.figure()
plt.imshow(wordcloud)
plt.axis("off")
plt.show()