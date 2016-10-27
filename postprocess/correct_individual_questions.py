import enchant
import json
import pickle
from nltk.tokenize import WordPunctTokenizer

import psycopg2

conn = psycopg2.connect('postgres://ojhcjubujbtgoz:qUx5vi7yR2j8KvjOsWd8LhN-RE@ec2-54-163-254-197.compute-1.amazonaws.com:5432/dd1rgn94b1f6e9')
cur = conn.cursor()

dialogues_file = 'guesswhat.jsonl'
correction_file = 'correction.pkl'
correction = pickle.load(open(correction_file))
correction['?'] = 0
correction[','] = 0
correction['\''] = 0
correction['/'] = 0
correction['pic'] = 'picture'
print len(correction)

d = enchant.Dict('en_US')
wpt = WordPunctTokenizer()

dictionary = {}
cnt = 0
with open(dialogues_file) as f:
    for line in f:
        dialogue = json.loads(line)
        for qa in dialogue['qas']:
            tokens = wpt.tokenize(qa['q'])
            incorr = False
            a = [len(tok) == 1 for tok in tokens]
            for i in range(0, len(a)-2):
                if a[i] and a[i+1] and tokens[i] != '\'' and tokens[i+1] != 's':
                    incorr = True

            for tok in tokens:
                tok = tok.lower()
                if not (d.check(tok) or (tok in correction and correction[tok] != '1')):
                    incorr = True

            if incorr:
                cnt += 1
                cur.execute("SELECT 1 FROM typo_question WHERE question_id = %s", [qa['id']])
                if cur.rowcount == 0:
                    cur.execute("INSERT INTO typo_question (question_id, content, round) VALUES(%s, %s, %s)",
                                [qa['id'], qa['q'], 2])

conn.commit()