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

""" Dictionaries for dialogue info that remains in RAM """
clients_waiting = {}  # Is client waiting?
clients_partner = {}  # Socketid of client's partner
clients_did = {}  # Dialogue id of client
dialogue_pic = {}  # Selected picture for dialogue: dialogue_id : Picture
dialogue_obj_ind = {}  # Selected index of objects: dialogue_id : list index

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
    sio.emit('new question', message,
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
def guess(sid):
    did = clients_did[sid]
    objs = [obj.to_json() for obj in dialogue_pic[did].objects]
    sio.emit('all annotations', {'partner': False, 'objs': objs},
             room=sid, namespace='/game')
    sio.emit('all annotations', {'partner': True},
             room=clients_partner[sid], namespace='/game')


@sio.on('guess annotation', namespace='/game')
def guess_annotation(sid, object_id):
    did = clients_did[sid]
    obj_ind = dialogue_obj_ind[did]
    selected_obj = dialogue_pic[did].objects[obj_ind]
    if selected_obj.object_id == object_id:
        sio.emit('correct annotation', {'partner': False},
                 room=sid, namespace='/game')
        sio.emit('correct annotation', {'partner': True},
                 room=clients_partner[sid], namespace='/game')
    else:
        guessed_obj = None
        for obj in dialogue_pic[did].objects:
            if obj.object_id == object_id:
                guessed_obj = obj
        sio.emit('wrong annotation', {'partner': False,
                                      'object': selected_obj.to_json()},
                 room=sid, namespace='/game')
        sio.emit('wrong annotation', {'partner': True,
                                      'object': guessed_obj.to_json()},
                 room=clients_partner[sid], namespace='/game')
    logout([sid, clients_partner[sid]])


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
        pic = db.get_picture(9)
        obj_ind = random.randint(0, len(pic.objects) - 1)
        obj = pic.objects[obj_ind]

        clients_did[id] = dialogue_id
        clients_did[sid] = dialogue_id
        dialogue_pic[dialogue_id] = pic
        dialogue_obj_ind[dialogue_id] = obj_ind

        if role:
            sio.emit('questioner',
                     {'img': pic.coco_url},
                     room=id,
                     namespace='/game')
            sio.emit('answerer',
                     {'img': pic.coco_url,
                      'object': obj.to_json()},
                     room=sid,
                     namespace='/game')
        else:
            sio.emit('answerer',
                     {'img': pic.coco_url,
                      'object': obj.to_json()},
                     room=id,
                     namespace='/game')
            sio.emit('questioner',
                     {'img': pic.coco_url},
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
