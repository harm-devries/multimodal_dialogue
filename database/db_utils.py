"""Helper functions to connect to postgres database."""
import psycopg2
import psycopg2.extras
import urlparse

from repoze.lru import lru_cache

from random import randint


global MIN_AREA
MIN_AREA = 50

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
        obj_dict['category'] = self.category[0].upper() + self.category[1:]
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
                         ' o.picture_id = %s AND o.area > %s '
                         ' ORDER BY o.area ASC'), [picture_id, MIN_AREA])

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



    def start_new_dialogue(self,
                           oracle_hit_id=None, oracle_worker_id=0,
                           questioner_hit_id=None, questioner_worker_id=0):

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

            dialogue_id = self.insert_dialogue(picture_id=picture_id, object_id=object_id,
                                               oracle_hit_id=oracle_hit_id, oracle_worker_id=oracle_worker_id,
                                               questioner_hit_id=questioner_hit_id, questioner_worker_id=questioner_worker_id)

            if dialogue_id is not None:
                dialogue = Dialogue(id=dialogue_id, picture=picture, object=objects[object_index])

        except Exception as e:
            print("Fail to start a new dialogue -> could not find object for picture (serial):" + str(picture_serial_id))
            print e

        return dialogue



    def insert_worker(self, worker_id):
        try:

            curr = self.conn.cursor()
            curr.execute(" INSERT INTO worker (worker_id) "
                         "  SELECT %s "
                         "  WHERE NOT EXISTS (SELECT 1 FROM worker WHERE worker_id=%s);",
                         (worker_id, worker_id))

            self.conn.commit()

        except Exception as e:
            print "Fail to insert new worker"
            print e



    def insert_hit(self, hit_id, worker_id):
        try:

            curr = self.conn.cursor()
            curr.execute(" INSERT INTO hit (hit_id, worker_id) VALUES (%s,%s);", (hit_id, worker_id))

            self.conn.commit()

        except Exception as e:
            print "Fail to insert new hit"
            print e



    def insert_dialogue(self, picture_id, object_id,
                        oracle_hit_id=None, oracle_worker_id=0,
                        questioner_hit_id=None, questioner_worker_id=0):

        try:

            # Insert oracle
            if oracle_hit_id is not None and oracle_worker_id > 0:
                self.insert_worker(worker_id=oracle_worker_id)
                self.insert_hit(hit_id=oracle_hit_id, worker_id=oracle_worker_id)
            else:
                oracle_hit_id = None

            # Insert questioner
            if questioner_hit_id is not None and questioner_worker_id > 0:
                self.insert_worker(worker_id=questioner_worker_id)
                self.insert_hit(hit_id=questioner_hit_id, worker_id=questioner_worker_id)
            else:
                questioner_hit_id = None

            # Insert dialogue
            curr = self.conn.cursor()
            curr.execute(" INSERT INTO dialogue (picture_id,object_id, oracle_hit_id, questioner_hit_id) "
                         " VALUES (%s,%s,%s,%s) "
                         " RETURNING dialogue_id; ",
                         (picture_id, object_id, oracle_hit_id, questioner_hit_id))

            self.conn.commit()

            dialogue_id, = curr.fetchone()

            return dialogue_id

        except Exception as e:
            print "Fail to insert new dialogue"
            print e



    def insert_question(self, dialogue_id, message):

        try:
            curr = self.conn.cursor()

            # Append a new question to the dialogue
            curr.execute("INSERT INTO question (dialogue_id,content) VALUES (%s,%s) "
                         "RETURNING question_id; ",
                         (dialogue_id, message))

            self.conn.commit()

            question_id, = curr.fetchone()

            return question_id

        except Exception as e:
            print "Fail to insert new question"
            print e



    def insert_answer(self, question_id, message):

        assert message == "Yes" or message == "No" or message == "N/A"

        try:
            curr = self.conn.cursor()

            # Append a new answer to the question
            curr.execute("INSERT INTO answer (question_id,content) VALUES (%s,%s) ", (question_id, message))

            self.conn.commit()

        except Exception as e:
            print "Fail to insert new answer"
            print e



    def insert_guess(self, dialogue_id, object_id):

        try:
            curr = self.conn.cursor()

            # Insert new guess
            curr.execute("INSERT INTO guess (dialogue_id, object_id) VALUES (%s,%s)", (dialogue_id, object_id))

            self.conn.commit()

        except Exception as e:
            print "Fail to insert new guess"
            print e



if __name__ == '__main__':

    db = DatabaseHelper(database="testdb", username="fstrub", password="21914218820*I!", hostname="localhost", port="5432")
    dialogue = db.start_new_dialogue(oracle_hit_id=randint(1, 10000), oracle_worker_id=randint(1, 4),
                                     questioner_hit_id=randint(1, 10000), questioner_worker_id=randint(1, 4))

    question_id = db.insert_question(dialogue_id=dialogue.id, message="Is it a car?")
    db.insert_answer(question_id=question_id, message="No")

    db.insert_guess(dialogue_id=dialogue.id, object_id=7385L)






