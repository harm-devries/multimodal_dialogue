"""Helper functions to connect to postgres database."""
import psycopg2
import psycopg2.extras
import urlparse

from repoze.lru import lru_cache

from random import randint


class Picture:
    """A picture object."""

    def __init__(self, picture_id, url, objects):
        self.id = picture_id
        self.coco_url = url
        self.objects = objects

    def to_json(self):
        """Convert picture object into json serializable dictionary"""
        pic_dict = {}
        pic_dict['picture_id'] = self.id
        pic_dict['coco_url'] = self.coco_url
        pic_dict['objects'] = [obj.to_json() for obj in self.objects]
        return pic_dict


class Object:
    """Object wrapper"""

    def __init__(self, object_id, category_id, category, segment, area ):
        self.object_id = object_id
        self.category_id = category_id
        self.category = category
        self.segment = Object.process_segment(segment)
        self.area = area

    @staticmethod
    def process_segment(segment):
        """Split coordinates into separate x and y coordinate lists.

        Pre:
           segment = list of polygons
           polygon = single list of coordinates
           e.g. [x_0, y_0, ..., x_n, y_n]

        Post:
           segment = list of polygons
           polygon['x'] = [x_0, ..., x_n]
           polygon['y'] = [y_0, ..., y_n]
        """
        segments = []
        for seg in segment:
            x = []
            y = []
            for i in range(0, len(seg), 2):
                x.append(seg[i])
                y.append(seg[i + 1])
            segments.append({'x': x, 'y': y})
        return segments

    def to_json(self):
        """Convert into json serializable dictionary.

        area: Numeric -> float
        """
        obj_dict = {}
        obj_dict['object_id'] = self.object_id
        obj_dict['category_id'] = self.category_id
        obj_dict['category'] = self.category
        # Numeric to float
        obj_dict['area'] = float(self.area)
        obj_dict['segment'] = self.segment

        return obj_dict


class Dialogue:
    def __init__(self, id, picture, object):
        self.id = id
        self.picture = picture
        self.object = object


class DatabaseHelper():
    """Database helper for multimodal dialogue project."""

    def __init__(self, database, username, password, hostname, port):

        """Connect to postgresql database."""
        try:
            self.conn = psycopg2.connect(database=database,
                                         user=username,
                                         password=password,
                                         host=hostname,
                                         port=port)
        except Exception as e:
            print "Unable to connect to database:"
            print e.msg



    @classmethod
    def from_postgresurl(cls, db_url):
        """Return DatabaseHelper from postgresurl.

        Parses postgresurl into database, username, password, hostname
        and port and initializes DatabaseHelper from it.
        """
        urlparse.uses_netloc.append("postgres")
        url = urlparse.urlparse(db_url)
        return cls(url.path[1:], url.username, url.password,
                   url.hostname, url.port)



    def get_picture(self, picture_id):
        """Fetch image by its id."""

        picture = None

        try:
            cur = self.conn.cursor()
            cur.execute(' SELECT coco_url FROM picture '
                        ' WHERE picture_id = %s', [picture_id])

            coco_url, = cur.fetchone()

            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute((' SELECT '
                         ' o.object_id, o.category_id, c.name, o.segment, '
                         ' o.area FROM object AS o, object_category AS c '
                         ' WHERE o.category_id = c.category_id AND '
                         ' o.picture_id = %s '
                         ' ORDER BY o.area ASC'), [picture_id])

            rows = cur.fetchall()
            objects = []
            for row in rows:
                obj = Object(row['object_id'], row['category_id'],
                             row['name'], row['segment'], row['area'])
                objects.append(obj)

            picture = Picture(picture_id=picture_id, url=coco_url, objects=objects)

        except Exception as e:
            print "Unable to get annotations"
            print e

        return picture



    @lru_cache(maxsize=1)
    def get_max_picture_id(self):
        try:
            curr = self.conn.cursor()
            curr.execute("SELECT MAX(serial_id) FROM picture;")

            return curr.fetchone()[0]

        except Exception as e:
            print "Fail to retrieve the number of picture --> abort"
            print e



    def start_new_dialogue(self):

        dialogue = None

        # Pick a random picture
        max_picture_id = self.get_max_picture_id()
        picture_serial_id = randint(1, max_picture_id)

        # Pick a random object
        try:
            curr = self.conn.cursor()

            curr.execute("SELECT picture_id FROM picture WHERE serial_id = %s;", [picture_serial_id])

            picture_id, = curr.fetchone()

            # retrieve all id from object rel
            picture = self.get_picture(picture_id=picture_id)

            # randomly picked one object
            objects = picture.objects
            object_index = randint(0, len(objects)-1)
            object_id = objects[object_index].object_id

            dialogue_id = self.insert_dialogue(picture_id=picture_id, object_id=object_id)

            if dialogue_id is not None:
                dialogue = Dialogue(id=dialogue_id, picture=picture, object=objects[object_index])

        except Exception as e:
            print("Fail to start a new dialogue -> could not find object for picture (serial):" + str(picture_serial_id))
            print e

        return dialogue



    def insert_dialogue(self,picture_id ,object_id ):

        try:
            curr = self.conn.cursor()
            curr.execute("INSERT INTO dialogue (picture_id,object_id) VALUES (%s,%s) "
                         "RETURNING dialogue_id; ",
                         (picture_id, object_id))

            self.conn.commit()

            dialogue_id = curr.fetchone()[0]

            return dialogue_id

        except Exception as e:
            print "Fail to insert new dialogue"
            print e



    def insert_question(self, hit_id, dialogue_id, message, worker_id = None):

        try:
            curr = self.conn.cursor()

            # Create a new hit
            curr.execute("INSERT INTO hit (hit_amazon_id,worker_amazon_id) VALUES (%s,%s) "
                         "RETURNING hit_id; ",
                         (hit_id, worker_id))

            hit_sql_id, = curr.fetchone()

            # Append a new question to the dialogue
            curr.execute("INSERT INTO question (hit_id,dialogue_id,content) VALUES (%s,%s,%s) "
                         "RETURNING question_id; ",
                         (hit_sql_id, dialogue_id, message))

            self.conn.commit()

            question_id, = curr.fetchone()

            return question_id

        except Exception as e:
            print "Fail to insert new dialogue"
            print e



    def insert_answer(self, hit_id, question_id, message, worker_id = None):

        assert message == "Yes" or message == "No" or message == "N/A"

        try:
            curr = self.conn.cursor()

            # Create a new hit
            curr.execute("INSERT INTO hit (hit_amazon_id,worker_amazon_id) VALUES (%s,%s) "
                         "RETURNING hit_id; ",
                         (hit_id, worker_id))

            hit_sql_id, = curr.fetchone()

            # Append a new question to the answer
            curr.execute("INSERT INTO answer (hit_id,question_id,content) VALUES (%s,%s,%s) ",
                         (hit_sql_id, question_id, message))

            self.conn.commit()

        except Exception as e:
            print "Fail to insert new dialogue"
            print e



    def insert_guess(self, dialogue_id, object_id):

        try:
            curr = self.conn.cursor()

            # Create a new hit
            curr.execute("INSERT INTO guess (dialogue_id, object_id) VALUES (%s,%s)", (dialogue_id, object_id))

            self.conn.commit()

        except Exception as e:
            print "Fail to insert new dialogue"
            print e



if __name__ == '__main__':

    import os
    db = DatabaseHelper.from_postgresurl(os.environ['DATABASE_URL'])

    dialogue = db.start_new_dialogue()

    question_id = db.insert_question(hit_id=randint(0, 10000000), worker_id=2, dialogue_id=dialogue.id, message="Is it a car?")
    db.insert_answer(hit_id = randint(0, 10000000), worker_id=3, question_id=question_id, message="No")

    db.insert_guess(dialogue_id=dialogue.id, object_id=7385L)






