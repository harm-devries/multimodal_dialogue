# import json
# from pprint import pprint
# import itertools
# import collections
# import logging
# import sys
# import pickle
# import numpy as np
# import re
#
# from gensim import corpora, models, similarities
#
# import matplotlib.pyplot as plt
#
# from sklearn.manifold import TSNE
#
#
#
# if len(sys.argv) > 1:
#     json_file = sys.argv[1]
# else:
#     json_file = 'guesswhat.json'
#
# # Retrieve thel ist of questions
# questions = []
# with open(json_file) as f:
#     for i, line in enumerate(f):
#         data = json.loads(line)
#         questions.append([d["q"] for d in data['qas']])
# questions = list(itertools.chain(*questions))
#
#
#
#
# logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
#
# stopwords = ["a", "an", "is", "it", "the", "does", "do", "are", "you", "that", "and",
#              "they", "doe", "this", "there", "hi", "his", "her", "its", "can", "he", "she", "us",  "?", "for"]
#
# texts = [[re.sub('[?]', '', word) for word in document.lower().split() if word not in stopwords and len(word) > 2]
#          for document in questions]
#
# # remove words that appear only once
# frequency = collections.Counter()
# for text in texts:
#     for token in text:
#         frequency[token] += 1
#
#
#
# texts = [[token for token in text if frequency[token] > 1 and len(token) > 0]
#          for text in texts]
#
# dictionary = corpora.Dictionary(texts)
#
# print("word2vec...")
# model = models.Word2Vec(texts, size=256, window=3, min_count=3, workers=4, iter=15)
#
#
# print("tsne...")
# tsne = TSNE(n_components=2, random_state=0, perplexity=30.0)
#
# word_embedding = [model[w] for w in model.vocab]
# tsne_out = tsne.fit_transform(word_embedding)
#
# print("save file...")
# with open("./word2vec.emb", "wb") as outfile:
#     dico_emb = {}
#     for tsne_2d, voc in zip(tsne_out, model.vocab):
#         dico_emb[voc] = {"tsne" : tsne_2d, "count" : frequency[voc], "embedding": model[voc]}
#     pickle.dump(dico_emb, file=outfile)
#
#
#
#
#
#
#
#
#
