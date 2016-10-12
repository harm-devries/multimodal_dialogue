import os
import psycopg2
import psycopg2.extras
import json
import pprint



from tqdm import tqdm






with open('guesswhat.json', 'w') as outfile:
    with psycopg2.connect('postgres://login:pwd@localhost:5432/dbname') as conn:

        print("Load dialogues... This should take less than 2 minutes ")
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cur.execute("""
            SELECT
                d.dialogue_id, d.picture_id, d.object_id, d.start_timestamp, d.mode, d.status,
                sq.worker_id,
                p.flickr_url, p.file_name, p.height, p.width, p.coco_url
                FROM dialogue d
                INNER JOIN session sq ON d.questioner_session_id = sq.id
                INNER JOIN session so ON d.oracle_session_id = so.id
                INNER JOIN picture p ON d.picture_id = p.picture_id
                WHERE
                d.prev_dialogue_id is NULL
                AND
                ((d.mode = 'qualification') OR (d.mode = 'normal' AND d.status = 'success'))
                ORDER BY d.dialogue_id ASC
        """)


        nr_of_dialogues = cur.rowcount

        rows = cur.fetchall()
        print(str(nr_of_dialogues) + "dialogues loaded")

        total_q = 0
        i = 0
        questioner_anonymous_id = {}

        print("Generate json... This should take between 30/60 minutes ")
        for row in tqdm(rows):

            dialogue = {}
            dialogue['dialogue_id'] = row['dialogue_id'] #wquestion -> recompute new id???
            #dialogue['mode'] = row[1] #Do we really need to put this feature?
            dialogue['picture_id'] = row['picture_id']
            dialogue['object_id'] = row['object_id']
            dialogue['timestamp'] = row['start_timestamp'].strftime("%Y-%m-%d %H:%M:%S")

            status = row['status']
            if status != "success" or status != "failure":
                dialogue['status'] = status
            else :
                dialogue['status'] = "unfinished"

            # Anonymise the amazon worker_id
            worker_id = row[7]
            questioner_anonymous_id[worker_id] = questioner_anonymous_id.get(worker_id, len(questioner_anonymous_id))
            dialogue['questioner_id'] = questioner_anonymous_id[worker_id]

            # Picture
            pict= {}
            pict["coco_url"] = row['coco_url']
            pict["flickr_url"] = row['flickr_url']
            pict["file_name"] = row['file_name']
            pict["height"] =  row['height']
            pict["width"] =  row['width']
            dialogue['picture'] = pict

            # Objects
            dialogue['objects'] = {}
            cur.execute(("""
                          SELECT  o.object_id, o.category_id, c.name, c.category_id, o.segment, o.area, o.is_crowd, o.bbox
                          FROM object AS o, object_category AS c
                         WHERE o.category_id = c.category_id AND o.picture_id = %s   ORDER BY o.area ASC; """)
                        , [dialogue['picture_id']])
            objects = cur.fetchall()

            dialogue['object'] = dict()
            for o in objects:
                obj = {}
                obj['object_id']   = int(o['object_id'])
                obj['category_id'] = int(o['category_id'])
                obj['category'] = o['name']
                obj['segment'] = o['segment']
                obj['bbox'] = o['bbox']
                obj['iscrowd'] = o['is_crowd']
                obj['area'] = float(o['area'])

                dialogue['object']["object_id"] = obj


        # When a questioner disconnect from an unfinished dialogue, his nect dialogue has the same target object
        # Here we fetch all question answer pairs from this dialogue and its precursors
        #    query = ("SELECT "
        #             "q.question_id, "
        #            "q.content, "
        #             "(SELECT answer.content FROM answer WHERE question_id = q.question_id ORDER BY timestamp DESC LIMIT 1) ans "
        #             "FROM "
        #             "question AS q, "
        #             "(WITH RECURSIVE t(dialogue_id, worker_id) AS ("
        #             "   SELECT d.dialogue_id, s.worker_id FROM dialogue d, session s WHERE d.questioner_session_id = s.id AND d.dialogue_id = %s "
        #             " UNION "
        #             " SELECT d2.dialogue_id, session.worker_id FROM dialogue d INNER JOIN dialogue d2 ON (d2.dialogue_id = d.prev_dialogue_id) INNER JOIN session ON (d2.questioner_session_id = session.id) INNER JOIN t ON (t.dialogue_id = d.dialogue_id AND t.worker_id = session.worker_id)"
        #             ") "
        #             "SELECT dialogue_id, worker_id FROM t) AS test "
        #             "WHERE q.dialogue_id IN (test.dialogue_id) AND (SELECT count(1) FROM answer WHERE question_id = q.question_id) > 0")

            query = ("""
            -- precompute some table

            WITH

            -- List all the dialogues dispatched in several dialogue
            RECURSIVE concatenate_dialogues(dialogue_id,next_dialogue_id) AS (
                SELECT d.dialogue_id,next_dialogue_id FROM dialogue d WHERE d.dialogue_id = %s --> dialogue id !!!
                    UNION
                SELECT child.dialogue_id, child.next_dialogue_id FROM concatenate_dialogues father
                INNER JOIN dialogue child ON father.next_dialogue_id = child.dialogue_id
            ),

            -- retrieve all the questions from a list of consecutive dialogues
            original_questions AS (
            SELECT * FROM question WHERE dialogue_id IN (SELECT dialogue_id FROM concatenate_dialogues)
            ),

            -- table that only contain the last fix of the questions (according timestamp)
            last_fixed_questions AS (
                  SELECT * FROM (SELECT p.question_id,
                                        p.corrected_text,
                                             ROW_NUMBER() OVER(PARTITION BY p.question_id
                                                                   ORDER BY p.timestamp DESC) AS rk
                                           FROM fixed_question p) t
                                           WHERE t.rk = 1 )

            -- Do the actual SQL statement to retrieve the complete dialogue
            SELECT q.question_id,
            COALESCE(corrected_text, q.content) question, -- pick the last fix if i exist, otherwise take the original content
            (SELECT answer.content FROM answer WHERE question_id = q.question_id ORDER BY timestamp DESC LIMIT 1) answer -- pick the latest answer (if oracle edit its answer)
            FROM original_questions q
            LEFT JOIN last_fixed_questions fq ON q.question_id = fq.question_id
            ORDER BY q.timestamp ASC """)

            cursor = conn.cursor()
            cursor.execute(query, [dialogue['dialogue_id']])
            questions = cursor.fetchall()
            total_q += cursor.rowcount

            qas = [{'id': q[0], 'q': q[1], 'a': q[2]} for q in questions]
            dialogue['qas'] = qas


            outfile.write(json.dumps(dialogue))
            outfile.write('\n')





