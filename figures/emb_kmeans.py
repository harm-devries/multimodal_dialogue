import json
from pprint import pprint
import itertools
import collections
import logging
import sys
import pickle
import numpy as np
import collections

import matplotlib.pyplot as plt

print("laod file...")
with open("./word2vec.emb", "rb") as f:
    dico = pickle.load(f)


frequency = collections.Counter()
tsne_emb = []
for word, values in dico.items():
    frequency[word] = values["count"]
    tsne_emb.append(values["tsne"])

tsne_emb = np.array(tsne_emb)




fig = plt.figure(figsize=(8, 3))
fig.subplots_adjust(left=0.02, right=0.98, bottom=0.05, top=0.9)
n_clusters = 50

from sklearn.cluster import MiniBatchKMeans, KMeans
from sklearn.metrics.pairwise import pairwise_distances_argmin
from sklearn.datasets.samples_generator import make_blobs


k_means = KMeans(init='k-means++', n_clusters=n_clusters, n_init=10)
k_means.fit(tsne_emb)

# Step size of the mesh. Decrease to increase the quality of the VQ.
h = .02     # point in the mesh [x_min, x_max]x[y_min, y_max].

# Plot the decision boundary. For that, we will assign a color to each
x_min, x_max = tsne_emb[:, 0].min() - 1, tsne_emb[:, 0].max() + 1
y_min, y_max = tsne_emb[:, 1].min() - 1, tsne_emb[:, 1].max() + 1
xx, yy = np.meshgrid(np.arange(x_min, x_max, h), np.arange(y_min, y_max, h))

# Obtain labels for each point in mesh. Use last trained model.
Z = k_means.predict(np.c_[xx.ravel(), yy.ravel()])



# Put the result into a color plot
Z = Z.reshape(xx.shape)
plt.figure(1)
plt.clf()
plt.imshow(Z, interpolation='nearest',
           extent=(xx.min(), xx.max(), yy.min(), yy.max()),
           cmap=plt.cm.Paired,
           aspect='auto', origin='lower')


plt.plot(tsne_emb[:, 0], tsne_emb[:, 1], 'k.', markersize=2)
# Plot the centroids as a white X
centroids = k_means.cluster_centers_
plt.scatter(centroids[:, 0], centroids[:, 1],
            marker='x', s=169, linewidths=3,
            color='w', zorder=10)




k_means_cluster_centers = np.sort(k_means.cluster_centers_, axis=0)
k_means_labels = pairwise_distances_argmin(tsne_emb, k_means_cluster_centers)
# KMeans
# for k in range(n_clusters):
#     my_members = k_means_labels == k
#     cluster_center = k_means_cluster_centers[k]
#     plt.plot(cluster_center[0], cluster_center[1], 'o', markerfacecolor=col, markeredgecolor='k', markersize=10)




mc_words = frequency.most_common(200)
mc_words = [w[0] for w in mc_words]

final_points = []
final_voc = []
for word, values in dico.items():
    if word in mc_words:
        final_points.append(values["tsne"])
        final_voc.append(word)
final_points = np.array(final_points)

for label, x, y in zip(final_voc, final_points[:, 0], final_points[:, 1]):
    plt.annotate(label, xy=(x, y), xytext=(0, 0), textcoords='offset points')

plt.title('K-means clustering on the digits dataset (PCA-reduced data)\n'
          'Centroids are marked with white cross')




plt.xlim(x_min, x_max)
plt.ylim(y_min, y_max)
plt.xticks(())
plt.yticks(())
plt.show()







#
#
#
# k_means_cluster_centers = np.sort(k_means.cluster_centers_, axis=0)
# k_means_labels = pairwise_distances_argmin(tsne_emb, k_means_cluster_centers)
#
#
#
#
#
# # We want to have the same colors for the same cluster from the
# # MiniBatchKMeans and the KMeans algorithm. Let's pair the cluster centers per
# # closest one.
#
#
# # Plot the decision boundary. For that, we will assign a color to each
# x_min, x_max = reduced_data[:, 0].min() - 1, reduced_data[:, 0].max() + 1
# y_min, y_max = reduced_data[:, 1].min() - 1, reduced_data[:, 1].max() + 1
# xx, yy = np.meshgrid(np.arange(x_min, x_max, h), np.arange(y_min, y_max, h))
#

# plt.show()
