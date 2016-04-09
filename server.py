import os
import psycopg2
import random
import socketio
import urlparse
from pymongo import MongoClient
from flask import Flask, render_template
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

""" Database connections """
client = MongoClient(os.environ['MONGODB_URL'])
db = client.coco.images

urlparse.uses_netloc.append("postgres")
url = urlparse.urlparse(os.environ["DATABASE_URL"])
conn = psycopg2.connect(database=url.path[1:],
                        user=url.username,
                        password=url.password,
                        host=url.hostname,
                        port=url.port)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/game')
def game():
    return render_template('game.html')


@sio.on('newquestion', namespace='/game')
def new_question(sid, message):
    curr = conn.cursor()
    curr.execute("INSERT INTO qa(dialogue_id, type, msg)"
                 "VALUES(%s, %s, %s)", (clients_did[sid],
                                        'q',
                                        message))
    conn.commit()
    sio.emit('newquestion', message,
             room=clients_partner[sid], namespace='/game')


@sio.on('new answer', namespace='/game')
def new_answer(sid, message):
    curr = conn.cursor()
    curr.execute("INSERT INTO qa(dialogue_id, type, msg)"
                 "VALUES(%s, %s, %s)", (clients_did[sid],
                                        'a',
                                        message))
    conn.commit()
    sio.emit('new answer', message,
             room=clients_partner[sid], namespace='/game')


@sio.on('guess', namespace='/game')
def guess(sid, obj):
    did = clients_did[sid]
    objs = [x for x in dialogue_anns[did]]
    sio.emit('all annotations', {'partner': False, 'objs': objs},
             room=sid, namespace='/game')
    sio.emit('all annotations', {'partner': True},
             room=clients_partner[sid], namespace='/game')


@sio.on('guess annotation', namespace='/game')
def guess_annotation(sid, ann_id):
    did = clients_did[sid]
    ann_ind = dialogue_annind[did]
    print type(ann_id)
    if dialogue_anns[did][ann_ind]['id'] == ann_id:
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


@sio.on('next', namespace='/game')
def find_partner(sid):
    partnerid = False
    for id, user in clients_waiting.items():
        if id != sid and user:
            partnerid = id

    if partnerid:
        clients_partner[partnerid] = sid
        clients_partner[sid] = partnerid
        role = (random.random() > 0.5)
        ind = random.randint(0, 1500)
        obj = db.find_one({'i': ind})
        ann_ind = random.randint(0, len(obj['annotations']) - 1)
        ann = obj['annotations'][ann_ind]

        curr = conn.cursor()
        curr.execute("INSERT INTO dialogues(image_id, ann_id) VALUES(%s, %s)",
                     (obj['id'], ann['id']))
        curr.execute("SELECT currval(pg_get_serial_sequence("
                     "'dialogues','id'))")
        dialogue_id, = curr.fetchone()
        conn.commit()
        clients_did[id] = dialogue_id
        clients_did[sid] = dialogue_id
        dialogue_anns[dialogue_id] = obj['annotations']
        dialogue_annind[dialogue_id] = ann_ind

        if role:
            sio.emit('questioner',
                     {'img': ('https://msvocds.blob.core.windows.net/'
                              'imgs/{}.jpg').format(obj['id'])},
                     room=id,
                     namespace='/game')
            sio.emit('answerer',
                     {'img': ('https://msvocds.blob.core.windows.net/'
                              'imgs/{}.jpg').format(obj['id']),
                      'poly_x': ann['poly_x'],
                      'poly_y': ann['poly_y'],
                      'name': ann['category'],
                      'catid': ann['catid']},
                     room=sid,
                     namespace='/game')
        else:
            sio.emit('answerer',
                     {'img': ('https://msvocds.blob.core.windows.net/'
                              'imgs/{}.jpg').format(obj['id']),
                      'poly_x': ann['poly_x'],
                      'poly_y': ann['poly_y'],
                      'name': ann['category'],
                      'catid': ann['catid']},
                     room=id,
                     namespace='/game')
            sio.emit('questioner',
                     {'img': ('https://msvocds.blob.core.windows.net/'
                              'imgs/{}.jpg').format(obj['id'])},
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
