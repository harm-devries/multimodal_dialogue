"""Helper functions to connect to postgres database."""
import psycopg2
import psycopg2.extras
import urlparse


class Picture():
    """A picture object."""

    def __init__(self, id, coco_url, objects):
        self.id = id
        self.coco_url = coco_url
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

    def __init__(self, object_id, category_id, category, segment, area):
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

    def get_picture(self, id):
        """Fetch image by its id."""
        try:
            cur = self.conn.cursor()
            cur.execute('SELECT coco_url FROM picture '
                        'WHERE picture_id = %s', [id])
            if cur.rowcount == 0:
                return None
            coco_url, = cur.fetchone()
            cur.close()
        except Exception as e:
            print "Unable to get image url from picture id"
            print e
        try:
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(('SELECT '
                         'o.object_id, o.category_id, c.name, o.segment, '
                         'o.area FROM object AS o, object_category AS c '
                         'WHERE o.category_id = c.category_id AND '
                         'o.picture_id = %s '
                         'ORDER BY o.area ASC'), [id])
            rows = cur.fetchall()
            objs = []
            for row in rows:
                obj = Object(row['object_id'], row['category_id'],
                             row['name'], row['segment'], row['area'])
                objs.append(obj)

        except Exception as e:
            print "Unable to get annotations"
            print e

        pic = Picture(id, coco_url, objs)
        return pic

    def insert_dialogue(self, picture_id, object_id):
        """Insert new dialogue."""
        # curr = self.conn.cursor()
        # curr.execute("INSERT INTO dialogue (picture_id, ann_id) "
        #              "VALUES(%s, %s)", (picture_id, object_id))
        # curr.execute("SELECT currval(pg_get_serial_sequence("
        #              "'dialogues','id'))")
        # self.conn.commit()
        raise NotImplementedError()

    def insert_question(self, hit_id, dialogue_id, message):
        """Insert new question."""
        raise NotImplementedError()

    def insert_answer(self, hit_id, dialogue_id, message):
        """Insert new answer."""
        raise NotImplementedError()

    def guess(self, hit_id, dialogue_id, ann_id):
        """Guess the object."""
        raise NotImplementedError()


if __name__ == '__main__':
    import os
    db = DatabaseHelper.from_postgresurl(os.environ['DATABASE_URL'])
    pic = db.get_picture(1000)
    if pic is None:
        print "No object found.."
    else:
        print pic.objects[0].category
