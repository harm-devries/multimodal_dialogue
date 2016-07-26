"""Helper functions to connect to postgres database."""
import datetime
from sqlalchemy.sql import text

from random import randint
from collections import defaultdict
from collections import namedtuple


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


class Dialogue:
    """Dialogue wrapper."""
    def __init__(self, id, picture, object):
        self.id = id
        self.picture = picture
        self.object = object
        self.question_ids = []
        self.oracle_sid = None
        self.questioner_sid = None
        self.turn = 'questioner'
        self.deadline = datetime.datetime.now() + datetime.timedelta(seconds=90)


def get_dialogues(connection):
    dialogues = []
    rows = connection.execute("SELECT d.dialogue_id, d.status, d.start_timestamp, d.end_timestamp, "
                              "(SELECT count(*) FROM question AS q WHERE q.dialogue_id = d.dialogue_id) AS nr_q, "
                              "(SELECT count(*) FROM object AS o WHERE o.picture_id = d.picture_id)"
                              " AS nr_o,  d.status, d.start_timestamp, d.end_timestamp FROM "
                              "dialogue AS d WHERE d.status != '' "
                              "ORDER BY d.start_timestamp DESC")
    for row in rows:
        seconds = -1
        if row[3] and row[2]:
            seconds = (row[3] - row[2]).seconds
        dialogues.append({'id': row[0], 'nr_objs': row[5],
                          'nr_q': row[4], 'status': row[1],
                          'seconds': seconds})
    return dialogues


def get_dialogue_stats(connection, mode='qualification'):
    rows = connection.execute(text("SELECT d.dialogue_id, d.status, d.start_timestamp, d.end_timestamp, "
                                   "(SELECT count(*) FROM question AS q WHERE q.dialogue_id = d.dialogue_id) AS nr_q, "
                                   "(SELECT count(*) FROM object AS o WHERE o.picture_id = d.picture_id)"
                                   " AS nr_o,  d.status, d.start_timestamp, d.end_timestamp FROM "
                                   "dialogue AS d WHERE d.mode = :mode "
                                   "ORDER BY d.start_timestamp DESC"),
                              mode=mode)

    counts = {'success': 0, 'failure': 0, 'ongoing': 0,
              'oracle_disconnect': 0, 'questioner_disconnect': 0,
              'oracle_timeout': 0, 'questioner_timeout': 0,
              'oracle_reported': 0, 'questioner_reported': 0,
              'total': 0}
    total_seconds = 0.
    total_questions = 0.
    j = 0
    for row in rows:
        counts[row[1]] += 1
        counts['total'] += 1
        if row[1] in ['success', 'failure']:
            total_seconds += (row[3] - row[2]).seconds
            total_questions += row[4]
            j += 1
    return counts, total_seconds / j, total_questions / j


def get_dialogue_guess(connection, dialogue_id):
    rows = connection.execute(text("SELECT "
                                   "o.object_id, o.category_id, c.name, o.segment, "
                                   "o.area FROM object AS o, object_category AS c, "
                                   "dialogue AS d, guess AS g "
                                   "WHERE o.category_id = c.category_id AND "
                                   "g.object_id = o.object_id AND "
                                   "g.dialogue_id = d.dialogue_id AND d.dialogue_id = :id "),
                              id=dialogue_id)
    if rows.rowcount > 0:
        row = rows.first()
        obj = Object(row[0], row[1],
                     row[2], row[3], row[4])
        return obj
    else:
        return None


def get_dialogue_object(connection, dialogue_id):
    rows = connection.execute(text("SELECT "
                                   "o.object_id, o.category_id, c.name, o.segment, "
                                   "o.area FROM object AS o, object_category AS c, "
                                   "dialogue AS d "
                                   "WHERE o.category_id = c.category_id AND "
                                   "d.object_id = o.object_id AND d.dialogue_id = :id "
                                   "ORDER BY o.area ASC; "),
                              id=dialogue_id)
    row = rows.first()
    obj = Object(row[0], row[1],
                 row[2], row[3], row[4])
    return obj


def get_dialogue_conversation(conn, dialogue_id):
    rows = conn.execute(text("SELECT q.content, a.content FROM question AS q, "
                             "answer AS a WHERE a.question_id = q.question_id "
                             "AND q.dialogue_id = :id ORDER BY q.timestamp DESC;"),
                        id=dialogue_id)

    return [dict(question=row[0], answer=row[1]) for row in rows]


def get_dialogue_info(conn, id):
    rows = conn.execute(text("SELECT p.picture_id, p.width, p.height, d.status, "
                             "(SELECT worker_id FROM session WHERE id = d.questioner_session_id), "
                             "(SELECT worker_id FROM session WHERE id = d.oracle_session_id), "
                             "d.start_timestamp, d.end_timestamp "
                             "FROM dialogue AS d, picture AS p "
                             "WHERE d.picture_id = p.picture_id "
                             "AND d.dialogue_id = :id"),
                        id=id)
    if rows.rowcount > 0:
        row = rows.first()
        seconds = -1
        if row[7] and row[6]:
            seconds = (row[7] - row[6]).seconds
        return row[0], row[1], row[2], row[3], row[4], row[5], seconds

    return None, None, None, None, None, None, None


def get_objects(conn, picture_id):
    rows = conn.execute(("SELECT "
                         "o.object_id, o.category_id, c.name, o.segment, "
                         "o.area FROM object AS o, object_category AS c "
                         "WHERE o.category_id = c.category_id AND "
                         "o.picture_id = %s "
                         "ORDER BY o.area ASC; "), [picture_id])
    objects = []
    for row in rows:
        obj = Object(row['object_id'], row['category_id'],
                     row['name'], row['segment'], row['area'])
        objects.append(obj)
    return objects


def get_random_picture(conn, difficulty=1):
    """Fetch random picture."""

    rows = conn.execute(text("SELECT picture_id, coco_url, width, height FROM "
                             "picture WHERE difficulty = :diff ORDER BY "
                             "RANDOM() LIMIT 1"), diff=difficulty)
    row = rows.first()
    picture_id, coco_url, width, height = row[0], row[1], row[2], row[3]

    objects = get_objects(conn, picture_id)

    return Picture(picture_id, coco_url, width, height, objects)


def get_last_unfinished_picture(conn, session_id, questioner=True):
    if questioner:
        result = conn.execute(text("SELECT d.status, d.object_id, d.picture_id, p.coco_url, p.width, p.height, d.dialogue_id "
                                   "FROM dialogue d, session s, picture p WHERE "
                                   "s.worker_id = (SELECT worker_id FROM session WHERE id = :sid) "
                                   "AND d.picture_id = p.picture_id AND d.questioner_session_id = s.id "
                                   "ORDER BY d.start_timestamp DESC LIMIT 1"), sid=session_id)
    else:
        result = conn.execute(text("SELECT d.status, d.object_id, d.picture_id, p.coco_url, p.width, p.height, d.dialogue_id "
                                   "FROM dialogue d, session s, picture p WHERE "
                                   "s.worker_id = (SELECT worker_id FROM session WHERE id = :sid) "
                                   "AND d.picture_id = p.picture_id AND d.oracle_session_id = s.id "
                                   "ORDER BY d.start_timestamp DESC LIMIT 1"), sid=session_id)
    if result.rowcount > 0:
        row = result.first()
        if row[0] in ['questioner_disconnect', 'oracle_disconnect', 'questioner_timeout', 'oracle_timeout']:
            objects = get_objects(conn, row[2])
            return Picture(row[2], row[3], row[4], row[5], objects), row[1], row[6]
    return None


def start_dialogue(conn, oracle_session_id, questioner_session_id,
                   difficulty=1, mode='qualification'):
    """Start new dialogue. """
    dialogue = None

    try:
        # If player disconnected during previous dialogue, 
        # we restart with the same image
        prev_dialogue = get_last_unfinished_picture(conn, questioner_session_id,
                                                    questioner=True)
        prev_dialogue_id = None
        if prev_dialogue is not None:
            picture, object_id, prev_dialogue_id = prev_dialogue
        else:
            prev_dialogue = get_last_unfinished_picture(conn, oracle_session_id,
                                                        questioner=False)
            if prev_dialogue is not None:
                picture, object_id, prev_dialogue_id = prev_dialogue
            else:
                picture = get_random_picture(conn, difficulty=difficulty)
                # Pick a random object
                objects = picture.objects
                object_index = randint(0, len(objects) - 1)
                object_id = objects[object_index].object_id

        obj = None
        for o in picture.objects:
            if o.object_id == object_id:
                obj = o

        dialogue_id = insert_dialogue(conn, picture.id,
                                      object_id,
                                      oracle_session_id,
                                      questioner_session_id,
                                      prev_dialogue_id,
                                      mode)

        if dialogue_id is not None:
            dialogue = Dialogue(id=dialogue_id, picture=picture,
                                object=obj)

    except Exception as e:
        print ("Fail to start a new dialogue -> could not find object")
        print (e)

    return dialogue


def insert_dialogue(conn, picture_id, object_id,
                    oracle_session_id,questioner_session_id,
                    prev_dialogue_id, mode):
    try:
        # Insert dialogue
        if prev_dialogue_id is None:
            result = conn.execute(text("INSERT INTO dialogue (picture_id, object_id, "
                                       "oracle_session_id, questioner_session_id, status, mode) "
                                       " VALUES (:pid, :oid, :osid, :qsid, 'ongoing', :mode) "
                                       " RETURNING dialogue_id; "),
                                  pid=picture_id, oid=object_id, osid=oracle_session_id,
                                  qsid=questioner_session_id, mode=mode)

            dialogue_id = result.first()[0]
            return dialogue_id
        else:
            result = conn.execute(text("INSERT INTO dialogue (picture_id, object_id, "
                                       "oracle_session_id, questioner_session_id, "
                                       "status, prev_dialogue_id, mode) "
                                       " VALUES (:pid, :oid, :osid, :qsid, 'ongoing', :prev_pid, :mode) "
                                       " RETURNING dialogue_id; "),
                                  pid=picture_id, oid=object_id, osid=oracle_session_id,
                                  qsid=questioner_session_id, prev_pid=prev_dialogue_id,
                                  mode=mode)

            dialogue_id = result.first()[0]
            return dialogue_id

    except Exception as e:
        print ("Fail to insert new dialogue")
        print (e)


def update_dialogue_status(conn, dialogue_id, status, reason=None):
    try:
        if reason is not None:
            conn.execute(text("UPDATE dialogue "
                              "SET status = :status, end_timestamp = NOW(), "
                              "reason = :reason "
                              "WHERE dialogue_id = :id;"),
                         status=status, reason=reason, id=dialogue_id)
        else:
            conn.execute(text("UPDATE dialogue "
                              "SET status = :status, end_timestamp = NOW() "
                              "WHERE dialogue_id = :id;"),
                         status=status, id=dialogue_id)
    except Exception as e:
        print ("Fail to update dialogue status")
        print (e)


def insert_question(conn, dialogue_id, message):
    try:
        # Append a new question to the dialogue
        result = conn.execute(text("INSERT INTO question (dialogue_id, content) "
                                   "VALUES (:id, :msg) RETURNING question_id; "),
                              id=dialogue_id, msg=message)

        question_id = result.first()[0]
        return question_id

    except Exception as e:
        print ("Fail to insert new question")
        print (e)


def insert_answer(conn, question_id, message):
    assert message == "Yes" or message == "No" or message == "N/A"

    try:
        # Append a new answer to the question
        result = conn.execute(text("INSERT INTO answer (question_id, content)"
                              "VALUES (:qid, :msg) RETURNING answer_id;"),
                              qid=question_id, msg=message)
        answer_id = result.first()[0]
        return answer_id

    except Exception as e:
        print ("Fail to insert new answer")
        print (e)


def insert_guess(conn, dialogue_id, object_id):
    try:
        # Insert new guess
        conn.execute(text("INSERT INTO guess (dialogue_id, object_id) "
                          "VALUES (:did, :oid);"),
                     did=dialogue_id, oid=object_id)

    except Exception as e:
        print ("Fail to insert new guess")
        print (e)


def insert_session(conn, player):
    try:
        conn.execute(text("INSERT INTO worker (id) "
                          "SELECT :id WHERE NOT EXISTS"
                          "(SELECT id FROM worker WHERE id = :id);"),
                     id=player.worker_id)

        conn.execute(text("INSERT INTO assignment (assignment_id, worker_id) "
                          "SELECT :ass_id, :worker_id WHERE NOT EXISTS"
                          "(SELECT assignment_id FROM assignment WHERE worker_id = :worker_id AND assignment_id = :ass_id);"),
                     worker_id=player.worker_id, ass_id=player.assignment_id)

        result = conn.execute(text("INSERT INTO session"
                                   "(socket_id, hit_id, assignment_id, worker_id, role, ip)"
                                   " VALUES(:sid, :hit_id, :ass_id, :worker_id, :role, :ip) "
                                   " RETURNING id;"),
                              sid=player.sid,
                              hit_id=player.hit_id,
                              ass_id=player.assignment_id,
                              worker_id=player.worker_id,
                              role=player.role,
                              ip=player.ip)

        session_id = result.first()[0]
        return session_id

    except Exception as e:
        print ("Fail to insert new session")
        print (e)


def update_session(conn, player):
    """Update session with assignmentId, hitId and workerId."""
    try:
        conn.execute(text("INSERT INTO worker (id) "
                          "SELECT :id WHERE NOT EXISTS"
                          "(SELECT id FROM worker WHERE id = :id);"),
                     id=player.worker_id)

        conn.execute(text("UPDATE session "
                          "SET assignment_id = :aid, hit_id = :hid, worker_id = :wid "
                          "WHERE id = :sid"),
                     aid=player.assignment_id,
                     hid=player.hit_id,
                     wid=player.worker_id,
                     sid=player.session_id)
    except Exception as e:
        print ("Fail to update session")
        print (e)


def end_session(conn, session_id):
    try:
        conn.execute(text("UPDATE session "
                          "SET end_timestamp = NOW() "
                          "WHERE id = :id; "),
                     id=session_id)

    except Exception as e:
        print ("Fail to end session, id = ", session_id)
        print (e)

def get_sessions(conn):

    sessions = []
    try:
        rows = conn.execute(" SELECT socket_id, worker_id, hit_id, assignment_id, ip, role  FROM session s "
                            " INNER JOIN "
                            "    ( SELECT oracle_session_id, questioner_session_id, status from dialogue WHERE status = 'ongoing') d "
                            "    ON d.oracle_session_id = s.id OR d.questioner_session_id = s.id ")
        for row in rows:
            session = dict()
            session["sid"] = row[0]
            session["worker_id"] = row[1]
            session["hit_id"] = row[2]
            session["assignment_id"] = row[3]
            session["ip"] = row[4]
            session["role"] = row[5]

            sessions.append(session)

    except Exception as e:
        print ("Fail to get sessions")
        print (e)

    return sessions

def insert_into_queue(conn, player):
    try:
        result = conn.execute(text("INSERT INTO queue_event"
                                   "(session_id)"
                                   " VALUES(:sid) RETURNING id;"),
                              sid=player.session_id)

        queue_id = result.first()[0]
        return queue_id
    except Exception as e:
        print ("Fail to insert queue")
        print (e)


def remove_from_queue(conn, player, reason):
    try:
        conn.execute(text("UPDATE queue_event "
                          "SET end_timestamp = NOW(), reason = :reason "
                          "WHERE id = :id"),
                     reason=reason,
                     id=player.queue_id)
        player.queue_id = None
    except Exception as e:
        print ("Fail to remove from queue")
        print (e)


Ongoing_worker = namedtuple('Ongoing_worker', ['socket_id', 'role'])
DEFAULT_ONGOING_WORKER = Ongoing_worker(socket_id=res[0], role=res[1])

def is_worker_playing(conn, id):
    try:
        result = conn.execute("SELECT socket_id, role FROM session s "
                              " INNER JOIN "
                              "  (SELECT oracle_session_id, questioner_session_id, status FROM dialogue WHERE status = 'ongoing') d "
                              " ON d.oracle_session_id = s.id OR d.questioner_session_id = s.id "
                              " WHERE worker_id = %s", [id])

        if result.rowcount > 0:
            res = result.first()
            return True, Ongoing_worker(socket_id=res[0], role=res[1])
        else:
            return False, DEFAULT_ONGOING_WORKER

    except Exception as e:
        print ("Fail to know whether the player is playing")
        print (e)
        return False, DEFAULT_ONGOING_WORKER



def get_ongoing_workers(conn):

    ongoing_workers = defaultdict(lambda: DEFAULT_ONGOING_WORKER)
    try:

        rows = conn.execute(" SELECT socket_id, worker_id, role  FROM session s "
                            " INNER JOIN "
                            "    ( SELECT oracle_session_id, questioner_session_id, status from dialogue WHERE status = 'ongoing') d "
                            "    ON d.oracle_session_id = s.id OR d.questioner_session_id = s.id ORDER BY worker_id")

        for row in rows:
            ongoing_workers[row[1]] = Ongoing_worker(socket_id=row[0], role=row[2])

    except Exception as e:
        print ("Fail to find workers who are playing")
        print (e)

    return ongoing_workers


def get_workers(conn):
    workers = []
    rows = conn.execute("SELECT w.worker_id, \
    (SELECT oracle_status FROM worker AS t WHERE t.id = w.worker_id ), \
    (SELECT questioner_status FROM worker AS t WHERE t.id = w.worker_id ), \
    (SELECT count(*) FROM session AS s, dialogue AS d WHERE s.worker_id = w.worker_id AND (d.oracle_session_id = s.id OR questioner_session_id = s.id) AND d.status = 'success') AS d_success, \
    (SELECT count(*) FROM session AS s, dialogue AS d WHERE s.worker_id = w.worker_id AND (d.oracle_session_id = s.id OR questioner_session_id = s.id) AND d.status = 'failure') AS d_failure, \
    (SELECT count(*) FROM session AS s, dialogue AS d WHERE s.worker_id = w.worker_id AND (d.oracle_session_id = s.id OR questioner_session_id = s.id) AND (d.status = 'oracle_disconnect' OR d.status = 'questioner_disconnect')) AS d_disconnect \
    FROM (SELECT worker_id FROM session AS s WHERE worker_id != '' GROUP BY worker_id) AS w ORDER BY d_success DESC")

    for row in rows:
        workers.append({'id': row[0], 'oracle_status' : row[1], 'questioner_status' : row[2], 'success': row[3],
                        'failure': row[4], 'disconnect': row[5]})
    return workers



def get_one_worker_status(conn, id):
    status = defaultdict(lambda: 'Error')
    try:
        rows = conn.execute("SELECT id, oracle_status, questioner_status, prev_oracle_status, prev_questioner_status FROM worker w WHERE w.id = %s", [id])
        row = rows.first()	
        status["id"] = row[0]
        status["oracle_status"] = row[1]
        status["questioner_status"] = row[2]
        status["prev_oracle_status"] = row[3]
        status["prev_questioner_status"] = row[4]
        
    except Exception as e:
        print ("Fail to load worker status")
        print (e)

    return status


def update_one_worker_status(conn, id, status_name, status):
    try:
        conn.execute("UPDATE worker SET " + status_name + " = %s WHERE id = %s", [status, id])

    except Exception as e:
        print ("Fail to update worker status")
        print (e)


def get_worker(conn, id):
    dialogues = []
    rows = conn.execute("SELECT d.dialogue_id, d.status, d.start_timestamp, d.end_timestamp, "
                        "(SELECT count(*) FROM question AS q WHERE q.dialogue_id = d.dialogue_id) AS nr_q, "
                        "(SELECT count(*) FROM object AS o WHERE o.picture_id = d.picture_id)"
                        " AS nr_o, (d.oracle_session_id = s.id) AS oracle FROM "
                        "dialogue AS d, session AS s WHERE (d.oracle_session_id = s.id OR d.questioner_session_id = s.id) "
                        "AND s.worker_id = %s AND d.status != '' "
                        "ORDER BY d.start_timestamp DESC", [id])
    for row in rows:
        seconds = -1
        if row[3] and row[2]:
            seconds = (row[3] - row[2]).seconds
        dialogues.append({'id': row[0], 'nr_objs': row[5],
                          'nr_q': row[4], 'status': row[1],
                          'seconds': seconds, 'oracle': row[6]})
    return dialogues


def get_recent_worker_stats(conn, id, limit=15, questioner=True):
    if questioner:
        stats = {'success': 0, 'failure': 0, 'questioner_disconnect': 0, 'questioner_timeout': 0}
    else:
        stats = {'success': 0, 'failure': 0, 'oracle_disconnect': 0, 'oracle_timeout': 0}
    if questioner:
        rows = conn.execute(text("SELECT status, count(status) FROM "
                                 "(SELECT status FROM dialogue WHERE status IN ('success', 'failure', 'questioner_timeout', 'questioner_disconnect') AND questioner_session_id IN"
                                 " (SELECT id FROM session WHERE worker_id = :wid) ORDER BY start_timestamp DESC LIMIT :limit)"
                                 " AS s GROUP BY status"), wid=id, limit=limit)
    else:
        rows = conn.execute(text("SELECT status, count(status) FROM "
                                 "(SELECT status FROM dialogue WHERE status IN ('success', 'failure', 'oracle_timeout', 'oracle_disconnect') AND oracle_session_id IN"
                                 " (SELECT id FROM session WHERE worker_id = :wid) ORDER BY start_timestamp DESC LIMIT :limit)"
                                 " AS s GROUP BY status"), wid=id, limit=limit)
    for row in rows:
        stats[row[0]] = int(row[1])
    return stats


def get_assignment_stats(conn, id, questioner=True):
    if questioner:
        stats = {'success': 0, 'failure': 0, 'questioner_disconnect': 0, 'questioner_timeout': 0}
    else:
        stats = {'success': 0, 'failure': 0, 'oracle_disconnect': 0, 'oracle_timeout': 0}
    if questioner:
        rows = conn.execute(text("SELECT status, count(status) FROM "
                                 "(SELECT status FROM dialogue WHERE status IN ('success', 'failure', 'questioner_timeout', 'questioner_disconnect') AND questioner_session_id IN"
                                 " (SELECT id FROM session WHERE assignment_id = :aid))"
                                 " AS s GROUP BY status"), aid=id)
    else:
        rows = conn.execute(text("SELECT status, count(status) FROM "
                                 "(SELECT status FROM dialogue WHERE status IN ('success', 'failure', 'oracle_timeout', 'oracle_disconnect') AND oracle_session_id IN"
                                 " (SELECT id FROM session WHERE assignment_id = :aid))"
                                 " AS s GROUP BY status"), aid=id)
    for row in rows:
        stats[row[0]] = int(row[1])
    return stats


def get_number_of_success(conn, id, questioner=False):
    result = conn.execute(text("SELECT count(*) FROM dialogue WHERE status = 'success'"
                               " AND questioner_session_id IN (SELECT id FROM session WHERE worker_id = :wid)"), wid=id)
    if result.rowcount > 0:
        return result.first()[0]
    else:
        return 0


def get_worker_status(conn, id, questioner=False):
    if questioner:
        result = conn.execute(text("SELECT questioner_status FROM worker WHERE id = :id"), id=id)
        if result.rowcount > 0:
            return result.first()[0]
    else:
        result = conn.execute(text("SELECT oracle_status FROM worker WHERE id = :id"), id=id)
        if result.rowcount > 0:
            return result.first()[0]
    return None


def assignment_completed(conn, assignment_id):
    result = conn.execute(text("SELECT completed FROM assignment WHERE assignment_id = :ass_id"),
                          ass_id=assignment_id)
    if result.rowcount > 0:
        return result.first()[0]
    return False
