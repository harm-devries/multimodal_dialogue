
import json
from pprint import pprint
import itertools
import collections
import sys
import re


if len(sys.argv) > 1:
    json_file = sys.argv[1]
else:
    json_file = 'guesswhat2.json'

stopwords = ["a", "an", "is", "it", "the", "does", "do", "are", "you", "that",
             "they", "doe", "this", "there", "hi", "his", "her", "its", "picture", "can", "he", "she", "bu", "us",
             "photo", "with", "one"]

words = collections.defaultdict(list)
number_words = collections.defaultdict(int)
dialogues = collections.defaultdict(list)


#Retrieve the dialogues
with open(json_file) as f:
    for i, line in enumerate(f):

        data = json.loads(line)

        if data["status"] != "success" and data["status"] != "failure":
            continue

        lenght = len(data['qas'])
        dialogues[lenght].append([d["q"] for d in data['qas']])





to_display = 10
for dialogue_size in range(3,12):

    #pick the dialogue wih the good lenght
    cur_dialogues = dialogues[dialogue_size]

    #initiate the word coutner for each depth of the dialogue
    word_counter = [collections.Counter() for _ in range(dialogue_size)]

    no_words = 0
    no_questions = 0

    # split questions into words and count the words
    for dialogue in cur_dialogues:
        for question, wc in zip(dialogue, word_counter):
            words = re.findall(r'\w+', re.sub('[?]', '', question))
            no_questions += 1
            for w in words:
                no_words += 1
                if len(w) > 2 and w not in stopwords:
                    wc[w.lower()] += 1

    # Generate the latex
    header = "\\begin{table}"
    header += "\\begin{tabular}{|l c|"
    for _ in range(1,dialogue_size): header+="l c c |"
    header += "}\n"
    header += "\\hline"
    header += "\n"

    body=""
    for i in range(to_display):
        for j in range(0, dialogue_size):
            word, occ = word_counter[j].most_common(i+1)[-1]
            body += word + " & {0:.2f} &".format(100.0*occ/no_questions)

            if j > 0:
                prev_words = [ w[0] for w in word_counter[j-1].most_common(to_display+1)]
                if   word in prev_words[:i] : body += "\\textbf{\\color{red}-}"
                elif word == prev_words[i]  : body += "="
                elif word in prev_words[i:] : body += "\\textbf{\\color{green}+}"
                else                        : body += "new"
                body += "& "

        body = body[:-2]
        body+= "\\\\ \n"

    footer = "\\hline\n"
    footer += "\\end{tabular}"
    footer += "\\caption{Dialogue of size "+ str(dialogue_size) + "}"
    footer += "\\end{table}"
    final = header + body + footer

    print(final)




