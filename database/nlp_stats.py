
import json
from pprint import pprint
import itertools


import matplotlib.pyplot as plt
import collections

from wordcloud import WordCloud
import numpy as np
import seaborn as sns

import re


json_file = 'guesswhat2.json'



qas = []
dialogues = []
pictures = {}
objects = {}

ratio_q_object = []


yes_no = []

number_yesno = {"yes" : 0, "no": 0, "NA" : 0}


with open(json_file) as f:
    for i, line in enumerate(f):

        data = json.loads(line)

        if data["status"] != "success" and data["status"] != "failure":
            continue



        pictures[data["picture_id"]] = 0
        objects[data["object_id"]] = 0
        qas.append(data['qas'])
        dialogues.append([d["q"] for d in data['qas']])



    #get the proportion of yes/no regarding the advance of the dialogue
        def convert(x, number):
            if   x == "Yes":
                number["yes"] +=1
                return 1
            elif x == "No":
                number["no"] += 1
                return 0
            else:
                number["NA"] += 1
                return 0.5


        yn = [ convert(_qas["a"],number_yesno) for _qas in data['qas'] ]
        x = np.linspace(0,1,len(yn))
        yes_no.append(np.array([x,yn]))

        ratio_q_object.append([len(data['objects']),len(data['qas'])])


ratio_q_object = np.array(ratio_q_object)
yes_no = np.concatenate([ys for ys in yes_no], axis=1).transpose()

questions = list(itertools.chain(*dialogues))

print("Number of dialogues: " + str(len(dialogues)))
print("Number of questions: " + str(len(questions)))
print("number of pictures:  " + str(len(pictures)))
print("number of objects:   " + str(len(objects)))
print(number_yesno)


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





sns.set(style="whitegrid")



# Set up the matplotlib figure
f, axes = plt.subplots(1,3 , figsize=(7, 7))
f.tight_layout(w_pad=0.5)

#ratio question/object
sns.distplot(w_by_q, norm_hist =True, kde=False, bins=np.arange(2.5, 15.5, 1), ax=axes[0], color="g")
axes[0].set_xlabel("Number of words")
axes[0].set_ylabel("Number of questions")

#ratio question/object
sns.despine(left=True)
sns.distplot(q_by_d, norm_hist =True, kde=False, bins=np.arange(0.5, 25.5, 1), ax=axes[1])
axes[1].set_xlabel("Number of question")
axes[1].set_ylabel("Number of dialogues")


x  = np.linspace(3, 25)
xx = np.linspace(3, 25, 80)
sns.regplot(x=ratio_q_object[:,0], y=ratio_q_object[:,1], x_bins=22, order=4, label="Human behavior", marker="." , ax=axes[2])
sns.regplot(x=xx, y=2*np.log2(xx), order=6, scatter=False, label="y = log2(x)", line_kws={'linestyle':'--'}, ax=axes[2])
sns.regplot(x=xx, y=xx           , order=1, scatter=False, label="y = x"      , line_kws={'linestyle':'--'}, ax=axes[2])

axes[2].legend(loc="best")
axes[2].set_xlim(3,25)
axes[2].set_ylim(0,20)
axes[2].set_xlabel("Number of objects")
axes[2].set_ylabel("Number of questions")

#sns.regplot(x=yes_no[:,0], y=yes_no[:,1], x_bins=10, order=3, label="Yes-no ratio", marker=".", truncate=True, ax=axes[3])

#axes[3].set_xlim(0,1)
#axes[3].set_ylim(0,1)
#axes[3].set_xlabel("ratio yes-no")
#axes[3].set_ylabel("Dialogue advancement")



plt.tight_layout()

plt.show()


def color_func(word=None, font_size=None, position=None,  orientation=None, font_path=None, random_state=None):
    color_list =["green",'blue', 'brown', "red", 'white', "black", "yellow", "color", "orange", "pink"]
    people_list  =['people', 'person', "he", "she", "human", "man", "woman", "guy", 'alive', "girl", "boy", "head", 'animal']
    prep = ['on', "in", 'of', 'to', "with", "by", "at", "or", "and", "from"]
    number = ['one', "two", "three", "four", "five", "six", "first", "second", "third", "half"]
    spatial = ["top", "left", "right", "side", "next", "front", "middle", "foreground", "bottom", "background",
               "near", "behind", "back", "at", "row", "far", "whole"]
    verb=["wearing", "have", "can", "holding", "sitting", "building", "standing", "see"]
    obj = ["hand","table", 'car', "food", "plate", "shirt", "something", "thing", "object",
           "light", "hat", "tree", "bag", "book", "sign", "bottle", "glas", "bus", "wall", "vehicle",
           "chair", "dog", "cat", "windows", "boat", "item", "shelf", "horse", "furniture", "water", "camera", "bike",
           "train", "window", "bowl", "plant", "ball"]
    misc = [ 'visible', "made", "part", "piece"]

    if word in color_list: return 'rgb(0, 102, 204)' #blue
    if word in people_list: return  'rgb(255, 0, 0)' #red
    if word in prep: return 'rgb(0, 153, 0)' #green
    if word in number: return 'rgb(255, 128, 0)' #orange
    if word in spatial: return 'rgb(204, 0, 102)' #purple
    if word in verb: return 'rgb(0, 204, 102)' #turquoise
    if word in obj: return 'rgb(64, 64, 64)' #grey
    if word in misc: return 'rgb(102, 102, 0)' #yellow
    else:
        print word
        return 'rgb(0, 0, 0)'  # orange
        #assert("Missing colors")



stopwords=["a","an","is","it","the","does","do","are","you","that",
           "they","doe", "this", "there", "hi", "his", "her", "its", "picture", "can", "he", "she"]

# take relative word frequencies into account, lower max_font_size
wordcloud = WordCloud(background_color="white", color_func=color_func, max_font_size=40, max_words=80,
                      stopwords=stopwords, prefer_horizontal=1, width=500, height=250)\
    .generate(" ".join(str(x) for x in word_list))



f.tight_layout()

plt.figure()
plt.imshow(wordcloud)
plt.axis("off")
plt.show()