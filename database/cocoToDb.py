import json
import psycopg2
import sys


training_file = 'annotations/instances_train2014.json'
validation_file = 'annotations/instances_val2014.json'

databasename = ""
login = ""
password = ""


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def loadCategories(cur, data):
    # 1  Insert categories
    supercategory = {}
    for category in data["categories"]:
        sc_name = category["supercategory"]
        supercategory[sc_name] = supercategory.get(
            sc_name, len(supercategory) + 1)

    # 1 create supercategory table
    print("inserting supercategories...")
    try:
        for name, index in supercategory.iteritems():
            cur.execute(
                "INSERT INTO object_supercategory (supercategory_id,name)"
                "VALUES (%s,%s)", (index, name))
    except Exception as error:
        print("supercategory could not be inserted, nothing was commited...")
        print error
        sys.exit()

    print("inserting categories...")
    # 1.2 Prepare category commit
    categories = data["categories"]
    for oneCategory in categories:
        oneCategory["supercategory_id"] = supercategory[
            oneCategory["supercategory"]]

    try:
        cur.executemany(
            "INSERT INTO object_category(category_id,supercategory_id,name)"
            "VALUES (%(id)s, %(supercategory_id)s, %(name)s)", categories)
    except Exception as error:
        print("category could not be inserted, nothing was commited...")
        print error
        sys.exit()


def loadPictures(cur, data):
    # 2 Insert pictures
    print("inserting picture...")
    pictures = data["images"]
    try:
        # split list into smaller chunk to perform a multiple insert SQL query
        # (http://stackoverflow.com/questions/8134602/psycopg2-insert-multiple-rows-with-one-query)
        for oneChunk in chunks(pictures, 500):
            queries = []
            # build tuples to insert
            for picture in oneChunk:
                queries.append((
                    picture["id"],
                    picture["coco_url"],
                    picture["flickr_url"],
                    picture["file_name"],
                    picture["height"],
                    picture["width"]))

            args_str = ','.join(
                cur.mogrify("(%s,%s,%s,%s,%s,%s)", q) for q in queries)
            if args_str:
                cur.execute(
                    "INSERT INTO picture(picture_id, coco_url, flickr_url,"
                    "file_name, height, width) VALUES " + args_str)

    except Exception as error:
        print("pictures could not be inserted, nothing was commited...")
        print error
        sys.exit()

    # 3 - Insert annotation
    print("inserting annotations...")
    annotations = data["annotations"]
    try:
        for oneChunk in chunks(annotations, 500):
            queries = []
            for oneAnnotation in oneChunk:
                queries.append((
                    oneAnnotation["id"],
                    oneAnnotation["image_id"],
                    oneAnnotation["category_id"],
                    json.dumps(oneAnnotation["segmentation"]),
                    json.dumps(oneAnnotation["bbox"]),
                    bool(oneAnnotation["iscrowd"]),
                    oneAnnotation["area"],
                ))

            args_str = ','.join(
                cur.mogrify("(%s,%s,%s,%s,%s,%s,%s)", q) for q in queries)
            cur.execute(
                "INSERT INTO object (object_id, picture_id, category_id,"
                "segment, bbox, is_crowd, area) VALUES " + args_str)

    except Exception as error:
        print("annotations could not be inserted, nothing was commited...")
        print error
        sys.exit()


try:
    # print("dbname='"+databasename+"' user='"+login+"' password='"+password+"'")
    conn = psycopg2.connect("dbname='testdb' user='fstrub'"
                            "host='localhost'password='21914218820*I!'")
except:
    print("I am unable to connect to the database.")
    sys.exit()
cur = conn.cursor()


print("loading training file...")
with open(training_file) as data_file:
    data = json.load(data_file)
    loadCategories(cur, data)
    loadPictures(cur, data)

print("loading validation file...")
with open(validation_file) as data_file:
    data = json.load(data_file)
    loadPictures(cur, data)

conn.commit()
