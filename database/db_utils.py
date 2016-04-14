"""Helper functions to connect to postgres database."""
import psycopg2
import psycopg2.extras
import urlparse

from repoze.lru import lru_cache

from random import randint


class Picture():
    """A picture object."""

    def __init__(self, picture_id = None, url = None, objects = []):
        self.id = id
        self.coco_url = url
        self.objects = objects

    def to_json(self):
        """Convert picture object into json serializable dictionary"""
        pic_dict = {}
        pic_dict['picture_id'] = self.id
        pic_dict['coco_url'] = self.coco_url
        pic_dict['objects'] = [obj.to_json() for obj in self.objects]
        return pic_dict




class Object():
    """Object wrapper"""

    def __init__(self, object_id = None, category_id = None, category = None, segment = None, area = None):
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


class Dialogue():
    def __init__(self, id = None, picture = None, object = None):
        assert id and picture and object
        self.id      = id
        self.picture = picture
        self.object  = object






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


###### WARNING this function does not work (category name is ignored) -> cf get_picture_for_dialogue
    # def get_picture(self, id):
    #     """Fetch image by its id."""
    #     try:
    #         cur = self.conn.cursor()
    #         cur.execute('SELECT coco_url FROM picture '
    #                     'WHERE picture_id = %s', [id])
    #         if cur.rowcount == 0:
    #             return None
    #         coco_url, = cur.fetchone()
    #         cur.close()
    #     except Exception as e:
    #         print "Unable to get image url from picture id"
    #         print e
    #     try:
    #         cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    #         cur.execute(('SELECT '
    #                      'o.object_id, o.category_id, c.name, o.segment, '
    #                      'o.area FROM object AS o, object_category AS c '
    #                      'WHERE o.category_id = c.category_id AND '
    #                      'o.picture_id = %s '
    #                      'ORDER BY o.area ASC'), [id])
    #         rows = cur.fetchall()
    #         objs = []
    #         for row in rows:
    #             obj = Object(row['object_id'], row['category_id'],
    #                          row['name'], row['segment'], row['area'])
    #             objs.append(obj)
    #
    #     except Exception as e:
    #         print "Unable to get annotations"
    #         print e
    #
    #
    #     return pic




    def get_picture_for_dialogue(self, dialogue_id = None, picture_id = None, object_id = None):
        """Fetch image by its id."""

        assert dialogue_id and picture_id and object_id

        dialogue = None

        try:
            cur = self.conn.cursor()

            cur.execute(' SELECT '
                        ' p.coco_url,'                     #picture info
                        ' o.object_id, o.segment, o.area,'  #object info
                        ' c.category_id, c.name'          #category info
                        ' FROM picture p'
                        '   INNER JOIN  '
                        '      (SELECT * FROM object WHERE picture_id =  %s) o'
                        '   ON p.picture_id = o.picture_id'
                        '   INNER JOIN '
                        '      object_category c '
                        '   ON c.category_id = o.category_id'
                        ' WHERE o.object_id = %s' , (picture_id, object_id))


            if cur.rowcount == 0: return None

            row = cur.fetchone()


            picture = Picture(picture_id = id, url = row[0])
            object = Object(object_id = row[1], segment = row[2], area = float(row[3]), category_id = int(row[4]),category = row[5])

            dialogue = Dialogue(id = dialogue_id, picture = picture, object = object)

        except Exception as e:
            print "Unable to get information for dialogue"
            print e

        return dialogue




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

            picture_id = curr.fetchone()[0]

            #retrieve all id from object rel
            curr.execute("SELECT object_id FROM object WHERE picture_id = %s;", [picture_id])
            objects = curr.fetchall()

            #randomly picked one id (there are not contiguous)
            object_id = long(objects[randint(0, curr.rowcount)-1][0])


            dialogue_id = self.insert_dialogue(picture_id = picture_id, object_id = object_id)

            if dialogue_id is not None:
                dialogue = self.get_picture_for_dialogue(dialogue_id, picture_id, object_id)

        except Exception as e:
            print("Fail to start a new dialogue -> could not find object for picture (serial):" + str(picture_serial_id))
            print e

        return dialogue




    def insert_dialogue(self, picture_id = None, object_id = None):

        assert picture_id and object_id

        try:
            curr = self.conn.cursor()
            curr.execute(   "INSERT INTO dialogue (picture_id,guess_id) VALUES (%s,%s) "
                            "RETURNING dialogue_id; ",
                            (picture_id, object_id))

            self.conn.commit()

            dialogue_id = curr.fetchone()[0]

            return dialogue_id


        except Exception as e:
            print "Fail to insert new dialogue"
            print e



    def insert_question(self, hit_id = None, worker_id = None, dialogue_id = None, message = None):

        assert hit_id and dialogue_id and message

        try:
            curr = self.conn.cursor()

            #Create a new hit
            curr.execute(   "INSERT INTO hit (hit_amazon_id,worker_amazon_id) VALUES (%s,%s) "
                            "RETURNING hit_id; ",
                            (hit_id, worker_id))

            hit_sql_id = curr.fetchone()[0]


            #Append a new question to the dialogue
            curr.execute(   "INSERT INTO question (hit_id,dialogue_id,content) VALUES (%s,%s,%s) "
                            "RETURNING question_id; ",
                            (hit_sql_id, dialogue_id, message))

            self.conn.commit()

            question_id = curr.fetchone()[0]

            return question_id

        except Exception as e:
            print "Fail to insert new dialogue"
            print e


    def insert_answer(self, hit_id = None, worker_id = None, question_id = None, message = None):

        assert hit_id and question_id and message
        assert message == "Yes" or message == "No" or message == "N/A"

        try:
            curr = self.conn.cursor()

            #Create a new hit
            curr.execute(   "INSERT INTO hit (hit_amazon_id,worker_amazon_id) VALUES (%s,%s) "
                            "RETURNING hit_id; ",
                            (hit_id, worker_id))

            hit_sql_id = curr.fetchone()[0]


            #Append a new question to the answer
            curr.execute(   "INSERT INTO answer (hit_id,question_id,content) VALUES (%s,%s,%s) ",
                            (hit_sql_id, question_id, message))

            self.conn.commit()

        except Exception as e:
            print "Fail to insert new dialogue"
            print e


if __name__ == '__main__':

    import os
    db = DatabaseHelper.from_postgresurl(os.environ['DATABASE_URL'])


    dialogue = db.start_new_dialogue()

    question_id = db.insert_question(hit_id = randint(0, 10000000), worker_id = 2, dialogue_id = dialogue.id, message = "Is it a car?")
    db.insert_answer(hit_id = randint(0, 10000000), worker_id = 3, question_id = question_id, message = "No")






