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
clients_dialogue = {}  # Dialogue client is involved in

""" Database connection """
db = DatabaseHelper.from_postgresurl(
    os.environ['HEROKU_POSTGRESQL_SILVER_URL'])


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/game')
def game():
    return render_template('game.html')


@sio.on('timeout', namespace='/game')
def time_out(sid):
    partnerid = clients_partner[sid]
    logout([sid, partnerid])
    find_partner(partnerid)
    sio.emit('partner timeout', '',
             room=partnerid, namespace='/game')


@sio.on('newquestion', namespace='/game')
def new_question(sid, message):
    dialogue = clients_dialogue[sid]
    dialogue.last_question_id = db.insert_question(dialogue.id, message)
    sio.emit('new question', message,
             room=clients_partner[sid], namespace='/game')


@sio.on('new answer', namespace='/game')
def new_answer(sid, message):
    dialogue = clients_dialogue[sid]
    db.insert_answer(dialogue.last_question_id, message)
    sio.emit('new answer', message,
             room=clients_partner[sid], namespace='/game')


@sio.on('guess', namespace='/game')
def guess(sid):
    dialogue = clients_dialogue[sid]
    objs = [obj.to_json() for obj in dialogue.picture.objects]
    sio.emit('all annotations', {'partner': False, 'objs': objs},
             room=sid, namespace='/game')
    sio.emit('all annotations', {'partner': True},
             room=clients_partner[sid], namespace='/game')


@sio.on('guess annotation', namespace='/game')
def guess_annotation(sid, object_id):
    dialogue = clients_dialogue[sid]
    db.insert_guess(dialogue.id, object_id)
    selected_obj = dialogue.object
    if selected_obj.object_id == object_id:
        sio.emit('correct annotation', {'partner': False},
                 room=sid, namespace='/game')
        sio.emit('correct annotation', {'partner': True},
                 room=clients_partner[sid], namespace='/game')
    else:
        for obj in dialogue.picture.objects:
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
        clients_partner[partnerid] = sid
        clients_partner[sid] = partnerid
        role = (random.random() > 0.5)

        if role:
            dialogue = db.start_dialogue()
            clients_dialogue[sid] = dialogue
            clients_dialogue[partnerid] = dialogue
            image_src = ('https://msvocds.blob.core.windows.net/imgs/'
                         '{}.jpg').format(dialogue.picture.id)
            sio.emit('questioner',
                     {'img': image_src},
                     room=id,
                     namespace='/game')
            sio.emit('answerer',
                     {'img': image_src,
                      'object': dialogue.object.to_json()},
                     room=sid,
                     namespace='/game')
        else:
            dialogue = db.start_dialogue()
            clients_dialogue[sid] = dialogue
            clients_dialogue[partnerid] = dialogue
            image_src = ('https://msvocds.blob.core.windows.net/imgs/'
                         '{}.jpg').format(dialogue.picture.id)
            sio.emit('answerer',
                     {'img': image_src,
                      'object': dialogue.object.to_json()},
                     room=id,
                     namespace='/game')
            sio.emit('questioner',
                     {'img': image_src},
                     room=sid,
                     namespace='/game')

        del clients_waiting[partnerid]
    else:
        clients_waiting[sid] = True


@sio.on('connect', namespace='/game')
def connect(sid, re):
    pass


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

        logout([sid, partnerid])
        find_partner(partnerid)


def logout(sids):
    for sid in sids:
        if sid in clients_partner:
            del clients_partner[sid]
        if sid in clients_dialogue:
            del clients_dialogue[sid]
