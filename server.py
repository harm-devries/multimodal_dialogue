import os
import random
import socketio
from flask import Flask, render_template
from database.db_utils import DatabaseHelper
# from flask.ext.login import LoginManager, UserMixin, login_required


# set this to 'threading', 'eventlet', or 'gevent'
async_mode = 'gevent'

if async_mode == 'gevent':
    from gevent import monkey
    monkey.patch_all()

sio = socketio.Server(logger=True, async_mode=async_mode)
app = Flask(__name__)
app.wsgi_app = socketio.Middleware(sio, app.wsgi_app)
app.config['SECRET_KEY'] = 'spywithmylittleeye!'

# sio = SocketIO(app)
# login_manager = LoginManager()
# login_manager.init_app(app)
""" Dictionaries for dialogue info that remains in RAM """
clients_waiting = {}  # Is client waiting?
clients_partner = {}  # Socketid of client's partner
clients_did = {}  # Dialogue id of client
dialogue_anns = {}  # All annotations for dialogue
dialogue_annind = {}  # Selected index of image annotations
""" Database connection """
db = DatabaseHelper.from_postgresurl(os.environ['DATABASE_URL'])


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/game')
def game():
    return render_template('game.html')


@sio.on('newquestion', namespace='/game')
def new_question(sid, message):
    # curr = conn.cursor()
    # curr.execute("INSERT INTO qa(dialogue_id, type, msg)"
    #              "VALUES(%s, %s, %s)", (clients_did[sid],
    #                                     'q',
    #                                     message))
    # conn.commit()
    sio.emit('newquestion', message,
             room=clients_partner[sid], namespace='/game')


@sio.on('new answer', namespace='/game')
def new_answer(sid, message):
    # curr = conn.cursor()
    # curr.execute("INSERT INTO qa(dialogue_id, type, msg)"
    #              "VALUES(%s, %s, %s)", (clients_did[sid],
    #                                     'a',
    #                                     message))
    # conn.commit()
    sio.emit('new answer', message,
             room=clients_partner[sid], namespace='/game')


@sio.on('guess', namespace='/game')
def guess(sid, obj):
    did = clients_did[sid]
    objs = dialogue_anns[did]
    sio.emit('all annotations', {'partner': False, 'objs': objs},
             room=sid, namespace='/game')
    sio.emit('all annotations', {'partner': True},
             room=clients_partner[sid], namespace='/game')


@sio.on('guess annotation', namespace='/game')
def guess_annotation(sid, ann_id):
    did = clients_did[sid]
    ann_ind = dialogue_annind[did]
    if dialogue_anns[did][ann_ind]['object_id'] == ann_id:
        sio.emit('correct annotation', {'partner': False},
                 room=sid, namespace='/game')
        sio.emit('correct annotation', {'partner': True},
                 room=clients_partner[sid], namespace='/game')
    else:
        sio.emit('wrong annotation', {'partner': False},
                 room=sid, namespace='/game')
        sio.emit('wrong annotation', {'partner': True},
                 room=clients_partner[sid], namespace='/game')
    logout([sid, clients_partner[sid]])


def process_annotations(annotations):
    """Preprocess annotations.

    Convert area attribute from Decimal to float
    because json encode can not handle Decimal.

    Also convert segment coordinates from a single list into
    x and y coordinate list.
    """
    anns = []
    for ann in annotations:
        ann = dict(ann)
        ann['area'] = float(ann['area'])

        segments = []
        for seg in ann['segment']:
            x = []
            y = []
            for i in range(0, len(seg), 2):
                x.append(seg[i])
                y.append(seg[i + 1])
            segments.append({'x': x, 'y': y})
        ann['segment'] = segments
        anns.append(ann)
    return anns

@sio.on('next', namespace='/game')
def find_partner(sid):
    partnerid = False
    for id, user in clients_waiting.items():
        if id != sid and user:
            partnerid = id

    if partnerid:
        dialogue_id = 1
        clients_partner[partnerid] = sid
        clients_partner[sid] = partnerid
        role = (random.random() > 0.5)
        coco_url, annotations = db.get_picture(9)
        annotations = process_annotations(annotations)
        ann_ind = random.randint(0, len(annotations) - 1)
        ann = annotations[ann_ind]

        clients_did[id] = dialogue_id
        clients_did[sid] = dialogue_id
        dialogue_anns[dialogue_id] = annotations
        dialogue_annind[dialogue_id] = ann_ind

        if role:
            sio.emit('questioner',
                     {'img': coco_url},
                     room=id,
                     namespace='/game')
            sio.emit('answerer',
                     {'img': coco_url,
                      'object': ann},
                     room=sid,
                     namespace='/game')
        else:
            sio.emit('answerer',
                     {'img': coco_url,
                      'object': ann},
                     room=id,
                     namespace='/game')
            sio.emit('questioner',
                     {'img': coco_url},
                     room=sid,
                     namespace='/game')

        del clients_waiting[partnerid]
    else:
        clients_waiting[sid] = True
        sio.emit('no partner',
                 {},
                 room=sid,
                 namespace='/game')


@sio.on('connect', namespace='/game')
def connect(sid, re):
    print 'connect' + sid


@sio.on('disconnect', namespace='/game')
def disconnect(sid):
    if sid in clients_waiting:
        del clients_waiting[sid]
    if sid in clients_partner:
        partnerid = clients_partner[sid]
        sio.emit('partner_disconnect',
                 '',
                 room=partnerid,
                 namespace='/game')

        find_partner(partnerid)
        logout([sid, partnerid])


def logout(sids):
    for sid in sids:
        if sid in clients_partner:
            del clients_partner[sid]
        if sid in clients_did:
            del clients_did[sid]
