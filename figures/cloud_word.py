

import json
from pprint import pprint
import itertools
import collections

import matplotlib.pyplot as plt
from wordcloud import WordCloud


import re


json_file = 'guesswhat2.json'


questions = []

with open(json_file) as f:
    for i, line in enumerate(f):

        data = json.loads(line)

        questions.append([d["q"] for d in data['qas']])

questions = list(itertools.chain(*questions))


# split questions into words
word_list = []
word_counter = collections.Counter()
for q in questions:
    q = re.sub('[?]', '', q)
    words = re.findall(r'\w+', q)
    word_list.append(words)

    for w in words:
        word_counter[w.lower()] += 1

pprint(word_counter)

word_list = list(itertools.chain(*word_list))


def color_func(word=None, font_size=None, position=None,  orientation=None, font_path=None, random_state=None):
    color_list =["green",'blue', 'brown', "red", 'white', "black", "yellow", "color", "orange", "pink"]
    people_list  =['people', 'person', "he", "she", "human", "man", "woman", "guy", 'alive', "girl", "boy", "head", 'animal']
    prep = ['on', "in", 'of', 'to', "with", "by", "at", "or", "and", "from"]
    number = ['one', "two", "three", "four", "five", "six", "first", "second", "third", "half"]
    spatial = ["top", "left", "right", "side", "next", "front", "middle", "foreground", "bottom", "background",
               "near", "behind", "back", "at", "row", "far", "whole", "closest"]
    verb=["wearing", "have", "can", "holding", "sitting", "building", "standing", "see"]
    obj = ["hand","table", 'car', "food", "plate", "shirt", "something", "thing", "object",
           "light", "hat", "tree", "bag", "book", "sign", "bottle", "glas", "bus", "wall", "vehicle",
           "chair", "dog", "cat", "windows", "boat", "item", "shelf", "horse", "furniture", "water", "camera", "bike",
           "train", "window", "bowl", "plant", "ball", "cup", ]
    misc = [ 'visible', "made", "part", "piece", "all"]

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
        return 'rgb(0, 0, 0)'
        #assert("Missing colors")



stopwords=["a","an","is","it","the","does","do","are","you","that",
           "they","doe", "this", "there", "hi", "his", "her", "its", "picture", "can", "he", "she", "bu", "us", "photo"]

# take relative word frequencies into account, lower max_font_size
wordcloud = WordCloud(background_color="white", color_func=color_func, max_font_size=40, max_words=80,
                      stopwords=stopwords, prefer_horizontal=1, width=500, height=350)\
    .generate(" ".join(str(x) for x in word_list))



plt.figure()
plt.imshow(wordcloud)
plt.axis("off")
plt.tight_layout()
plt.show()