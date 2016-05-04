"""Helper functions to connect to postgres database."""
import os
import psycopg2
import psycopg2.extras
import urlparse

from random import randint


class Picture:
    """A picture object."""

    def __init__(self, picture_id, url, width, height, objects):
        self.id = picture_id
        self.width = width
        self.height = height
        self.coco_url = url
        self.objects = objects

    def to_json(self):
        """Convert picture object into json serializable dictionary"""
        pic_dict = {}
        pic_dict['picture_id'] = self.id
        pic_dict['width'] = self.width
        pic_dict['height'] = self.height
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
    """Dialogue wrapper."""
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
            print e

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


    def get_conversation(self, dialogue_id):
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT q.content, a.content FROM question AS q, answer AS a "
                        "WHERE a.question_id = q.question_id and q.dialogue_id = %s "
                        "ORDER BY q.timestamp DESC", [dialogue_id])

            rows = cur.fetchall()
            qas = [dict(question=row[0], answer=row[1]) for row in rows]
            cur.close()
        except Exception as e:
            print e
        return qas

    def get_random_picture(self, difficulty=1):

        """Fetch image by its id."""

        picture = None

        try:
            cur = self.conn.cursor()
            cur.execute("SELECT picture_id, coco_url, width, height FROM "
                        "picture WHERE difficulty = %s ORDER BY "
                        "RANDOM() LIMIT 1", [difficulty])

            picture_id, coco_url, width, height = cur.fetchone()
            cur.close()

            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            cur.execute(("SELECT "
                         "o.object_id, o.category_id, c.name, o.segment, "
                         "o.area FROM object AS o, object_category AS c "
                         "WHERE o.category_id = c.category_id AND "
                         "o.picture_id = %s "
                         "ORDER BY o.area ASC"), [picture_id])

            rows = cur.fetchall()
            objects = []
            for row in rows:
                obj = Object(row['object_id'], row['category_id'],
                             row['name'], row['segment'], row['area'])
                objects.append(obj)

            picture = Picture(picture_id, coco_url, width, height, objects)

        except Exception as e:
            print "Unable to fetch picture"
            print e

        return picture

    def start_dialogue(self, oracle_hit_id=None, oracle_worker_id=None,
                       questioner_hit_id=None, questioner_worker_id=None):
        """Start new dialogue. """
        dialogue = None

        try:
            # Pick a random picture
            picture = self.get_random_picture()

            # Pick a random object
            objects = picture.objects
            object_index = randint(0, len(objects) - 1)
            object_id = objects[object_index].object_id

            dialogue_id = self.insert_dialogue(
                picture_id=picture.id,
                object_id=object_id,
                oracle_hit_id=oracle_hit_id,
                oracle_worker_id=oracle_worker_id,
                questioner_hit_id=questioner_hit_id,
                questioner_worker_id=questioner_worker_id)

            if dialogue_id is not None:
                dialogue = Dialogue(id=dialogue_id, picture=picture,
                                    object=objects[object_index])

        except Exception as e:
            print("Fail to start a new dialogue -> could not find object")
            print e

        return dialogue

    def insert_dialogue(self, picture_id, object_id,
                        oracle_hit_id=None, oracle_worker_id=0,
                        questioner_hit_id=None, questioner_worker_id=0):
        try:
            # Insert oracle
            if oracle_hit_id is not None and oracle_worker_id > 0:
                self.insert_worker(worker_id=oracle_worker_id)
                self.insert_hit(hit_id=oracle_hit_id,
                                worker_id=oracle_worker_id)
            else:
                oracle_hit_id = None

            # Insert questioner
            if questioner_hit_id is not None and questioner_worker_id > 0:
                self.insert_worker(worker_id=questioner_worker_id)
                self.insert_hit(hit_id=questioner_hit_id,
                                worker_id=questioner_worker_id)
            else:
                questioner_hit_id = None

            # Insert dialogue
            curr = self.conn.cursor()
            curr.execute("INSERT INTO dialogue (picture_id, object_id, "
                         "oracle_hit_id, questioner_hit_id) "
                         " VALUES (%s,%s,%s,%s) "
                         " RETURNING dialogue_id; ",
                         (picture_id, object_id, oracle_hit_id,
                          questioner_hit_id))

            self.conn.commit()

            dialogue_id, = curr.fetchone()

            return dialogue_id

        except Exception as e:
            self.conn.rollback()
            print "Fail to insert new dialogue"
            print e

    def insert_worker(self, worker_id):
        try:
            curr = self.conn.cursor()
            curr.execute("INSERT INTO worker (worker_id) "
                         "SELECT %s "
                         "WHERE NOT EXISTS"
                         "(SELECT 1 FROM worker WHERE worker_id=%s);",
                         (worker_id, worker_id))

            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print "Fail to insert new worker"
            print e

    def insert_hit(self, hit_id, worker_id):
        try:

            curr = self.conn.cursor()
            curr.execute("INSERT INTO hit (hit_id, worker_id) "
                         "VALUES (%s,%s);", (hit_id, worker_id))

            self.conn.commit()
        except Exception as e:
            if curr is not None:
                curr.rollback()
            print "Fail to insert new hit"
            print e

    def insert_question(self, dialogue_id, message):

        try:
            curr = self.conn.cursor()

            # Append a new question to the dialogue
            curr.execute("INSERT INTO question (dialogue_id, content) "
                         "VALUES (%s,%s) RETURNING question_id; ",
                         (dialogue_id, message))

            self.conn.commit()

            question_id, = curr.fetchone()

            return question_id

        except Exception as e:
            self.conn.rollback()
            print "Fail to insert new question"
            print e

    def insert_answer(self, question_id, message):
        assert message == "Yes" or message == "No" or message == "N/A"

        try:
            curr = self.conn.cursor()

            # Append a new answer to the question
            curr.execute("INSERT INTO answer (question_id, content)"
                         "VALUES (%s,%s) RETURNING answer_id;", (question_id, message))
            self.conn.commit()

            answer_id, = curr.fetchone()

            return answer_id

        except Exception as e:
            self.conn.rollback()
            print "Fail to insert new answer"
            print e

    def insert_guess(self, dialogue_id, object_id):
        try:
            curr = self.conn.cursor()

            # Insert new guess
            curr.execute("INSERT INTO guess (dialogue_id, object_id)"
                         "VALUES (%s,%s)", (dialogue_id, object_id))

            self.conn.commit()

        except Exception as e:
            self.conn.rollback()
            print "Fail to insert new guess"
            print e

    # def insert_name(self, name):
    #     try:
    #         curr = self.conn.cursor()

    #         # Insert new guess
    #         curr.execute("INSERT INTO player"
    #                      "(name) "
    #                      "SELECT %s WHERE "
    #                      "NOT EXISTS ("
    #                      "SELECT name FROM player "
    #                      "WHERE name = %s);", [name, name])

    #         self.conn.commit()

    #     except Exception as e:
    #         self.conn.rollback()
    #         print "Fail to insert new player"
    #         print e

    def insert_report_worker(self, dialogue_id, from_worker_id,
                             to_worker_id, from_oracle, content=None,
                             too_slow=False, harassment=False,
                             bad_player=False):
        try:
            curr = self.conn.cursor()

            # Insert new guess
            curr.execute("INSERT INTO report_worker "
                         "(dialogue_id, from_worker_id, to_worker_id, "
                         "from_oracle, content, too_slow, harassment, "
                         "bad_player) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ",
                         [dialogue_id, from_worker_id, to_worker_id,
                          from_oracle, content, too_slow, harassment,
                          bad_player])

        except Exception as e:
            self.conn.rollback()
            print("Fail to insert report to blame worker (" +
                  str(to_worker_id) + ") for dialogue (" +
                  str(dialogue_id) + ")")
            print e

    # TODO use trigger to compute from_oracle on the fly
    def insert_report_dialogue(self, dialogue_id, worker_id, from_oracle,
                               content=None, picture_too_hard=False,
                               object_too_hard=False):
        try:
            curr = self.conn.cursor()

            # Insert new guess
            curr.execute("INSERT INTO report_dialogue "
                         "(dialogue_id, worker_id, from_oracle, content, "
                         "picture_too_hard, object_too_hard) "
                         "VALUES (%s,%s,%s,%s,%s,%s) ",
                         [dialogue_id, worker_id, from_oracle, content,
                          picture_too_hard, object_too_hard])

        except Exception as e:
            self.conn.rollback()
            print("Fail to insert report from worker (" + str(worker_id) +
                  ") for dialogue (" + str(dialogue_id) + ")")
            print e

    def update_answer(self, answer_id, message):

        assert message == "Yes" or message == "No" or message == "N/A"

        try:
            curr = self.conn.cursor()

            # Insert new guess
            curr.execute("UPDATE answer SET content = %s WHERE answer_id = %s",
                         [message, answer_id])

            self.conn.commit()

        except Exception as e:
            self.conn.rollback()
            print "Fail to update answer"
            print e

    # def update_score(self, name):
    #     try:
    #         curr = self.conn.cursor()

    #         # Insert new guess
    #         curr.execute("UPDATE player SET score = score + 10 WHERE name = %s", [name])

    #         self.conn.commit()

    #     except Exception as e:
    #         self.conn.rollback()
    #         print "Fail to update score"
    #         print e

if __name__ == '__main__':

    db = DatabaseHelper.from_postgresurl(
        os.environ['HEROKU_POSTGRESQL_SILVER_URL'])

    dialogue = db.start_dialogue(oracle_hit_id=10, oracle_worker_id=10,
                                 questioner_hit_id=20, questioner_worker_id=20)

    question_id = db.insert_question(dialogue_id=dialogue.id,
                                     message="Is it a car?")

    answer_id = db.insert_answer(question_id=question_id, message="No")
    db.update_answer(answer_id=answer_id, message="Yes")
    db.insert_guess(dialogue_id=dialogue.id,
                    object_id=dialogue.object.object_id)

    db.insert_report_dialogue(dialogue_id=dialogue.id,
                              worker_id=10, from_oracle=True,
                              content=None, picture_too_hard=False,
                              object_too_hard=True)

    db.insert_report_worker(dialogue_id=dialogue.id, from_worker_id=20,
                            to_worker_id=10, from_oracle=False,
                            content="keep insulting me - no question",
                            too_slow=False, harassment=True, bad_player=True)
