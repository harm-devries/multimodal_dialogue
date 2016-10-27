import psycopg2
import seaborn as sns
import matplotlib.pyplot as plt
import numpy

conn = psycopg2.connect('postgres://ojhcjubujbtgoz:qUx5vi7yR2j8KvjOsWd8LhN-RE@ec2-54-163-254-197.compute-1.amazonaws.com:5432/dd1rgn94b1f6e9')
cur = conn.cursor()

cur.execute("SELECT area FROM object")

areas = []
for row in cur.fetchall():
	areas.append(float(row[0]))

areas2 = []
cur.execute("SELECT o.area FROM object AS o, dialogue AS d WHERE d.object_id = o.object_id AND d.mode = 'normal' AND d.status = 'success' ")
for row in cur.fetchall():
	areas2.append(float(row[0]))

sns.despine(left=True)
sns.distplot(areas, norm_hist=True, kde=False, bins=numpy.arange(0, 5e4, 1000), label="MS Coco")
sns.distplot(areas2, norm_hist=True, kde=False, bins=numpy.arange(0, 5e4, 1000), color="g", label="GuessWhat?!")

plt.xlabel('Object area')
plt.ylabel('Density')
plt.legend()
plt.show()
