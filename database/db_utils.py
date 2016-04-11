"""Helper functions to connect to postgres database."""
import psycopg2
import psycopg2.extras
import urlparse


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
        """Get image_url and its annotations by picture_id."""
        try:
            cur = self.conn.cursor()
            cur.execute('SELECT coco_url FROM picture '
                        'WHERE picture_id = %s', [id])
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
        except Exception as e:
            print "Unable to get annotations"
            print e

        return coco_url, rows

    def insert(self, picture_id, object_id):
        """Insert new dialogue."""
        # curr = self.conn.cursor()
        # curr.execute("INSERT INTO dialogue (picture_id, ann_id) "
        #              "VALUES(%s, %s)", (picture_id, object_id))
        # curr.execute("SELECT currval(pg_get_serial_sequence("
        #              "'dialogues','id'))")
        # self.conn.commit()
        raise NotImplementedError()


if __name__ == '__main__':
    import os
    db = DatabaseHelper.from_postgresurl(os.environ['DATABASE_URL'])
    url, annotations = db.get_picture(9)
    print annotations[0].keys()
