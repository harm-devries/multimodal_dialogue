import os
import socketio
from collections import deque
from flask import Flask, render_template
from database.db_utils import DatabaseHelper
from players import Oracle, Questioner1, Questioner2
# from flask.ext.login import LoginManager, UserMixin, login_required

# set this to 'threading', 'eventlet', or 'gevent'
async_mode = 'gevent'

if async_mode == 'gevent':
    from gevent import monkey
    monkey.patch_all()
if async_mode == 'eventlet':
    import eventlet
    eventlet.monkey_patch()

sio = socketio.Server(logger=True, async_mode=async_mode)
app = Flask(__name__)
app.wsgi_app = socketio.Middleware(sio, app.wsgi_app)
app.config['SECRET_KEY'] = 'spywithmylittleeye!'

""" Dictionaries for dialogue info that remains in RAM """
oracle_queue = deque()
questioner_queue = deque()

players = {}  # indexed by socket id
clients_dialogue = {}  # Dialogue client is involved in


""" Database connection """
db = DatabaseHelper.from_postgresurl(
    os.environ['HEROKU_POSTGRESQL_SILVER_URL'])


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/oracle')
def oracle():
    return render_template('oracle.html')


@app.route('/questioner1')
def questioner1():
    return render_template('questioner1.html')


@app.route('/questioner2')
def questioner2():
    return render_template('questioner2.html')


@app.route('/dialogue/<id>')
def show_dialogue(id):
    cur = db.conn.cursor()
    cur.execute("SELECT picture_id FROM dialogue WHERE dialogue_id = %s", [id])
    picture_id, = cur.fetchone()
    image = ('https://msvocds.blob.core.windows.net/imgs/'
             '{}.jpg').format(picture_id)
    return render_template('dialogue.html',
                           qas=db.get_conversation(id),
                           image=image)


@sio.on('timeout', namespace='/oracle')
def time_out(sid):
    player = players[sid]
    partnerid = player.partner_sid
    delete_game([sid, partnerid])
    sio.emit('partner timeout', '',
             room=partnerid, namespace='/game')
    if players[partnerid].role == 'questioner':
        find_oracle(partnerid)
    else:
        find_questioner(partnerid)


@sio.on('newquestion', namespace='/questioner1')
def new_question(sid, message):
    player = players[sid]
    dialogue = clients_dialogue[sid]
    dialogue.last_question_id = db.insert_question(dialogue.id, message)
    sio.emit('new question', message,
             room=player.partner_sid, namespace='/oracle')


@sio.on('new answer', namespace='/oracle')
def new_answer(sid, message):
    player = players[sid]
    partner = players[player.partner_sid]
    dialogue = clients_dialogue[sid]
    db.insert_answer(dialogue.last_question_id, message)
    sio.emit('new answer', message,
             room=partner.sid, namespace=partner.namespace)


@sio.on('guess', namespace='/questioner1')
def guess(sid):
    player = players[sid]
    dialogue = clients_dialogue[sid]
    objs = [obj.to_json() for obj in dialogue.picture.objects]
    sio.emit('all annotations', {'partner': False, 'objs': objs},
             room=sid, namespace=player.namespace)
    sio.emit('all annotations', {'partner': True},
             room=player.partner_sid, namespace='/oracle')


@sio.on('guess annotation', namespace='/questioner1')
def guess_annotation(sid, object_id):
    player = players[sid]
    dialogue = clients_dialogue[sid]
    db.insert_guess(dialogue.id, object_id)
    selected_obj = dialogue.object
    if selected_obj.object_id == object_id:
        # db.update_score(player.name)
        # db.update_score(players[player.partner_sid].name)
        sio.emit('correct annotation', {'partner': False,
                                        'object': selected_obj.to_json()},
                 room=sid, namespace=player.namespace)
        sio.emit('correct annotation', {'partner': True,
                                        'object': selected_obj.to_json()},
                 room=player.partner_sid, namespace='/oracle')
    else:
        for obj in dialogue.picture.objects:
            if obj.object_id == object_id:
                guessed_obj = obj
        sio.emit('wrong annotation', {'partner': False,
                                      'object': selected_obj.to_json()},
                 room=sid, namespace=player.namespace)
        sio.emit('wrong annotation', {'partner': True,
                                      'object': guessed_obj.to_json()},
                 room=player.partner_sid, namespace='/oracle')
    delete_game([player.sid, player.partner_sid])


@sio.on('next questioner', namespace='/oracle')
def find_questioner(sid):
    partner = False
    player = players[sid]

    if len(questioner_queue) > 0:
        partner = questioner_queue.pop()

    if partner:
        partner.partner_sid = player.sid
        player.partner_sid = partner.sid

        dialogue = db.start_dialogue()
        clients_dialogue[sid] = dialogue
        clients_dialogue[partner.sid] = dialogue
        image_src = ('https://msvocds.blob.core.windows.net/imgs/'
                     '{}.jpg').format(dialogue.picture.id)
        sio.emit('questioner',
                 {'img': {'src': image_src,
                          'width': dialogue.picture.width,
                          'height': dialogue.picture.height}},
                 room=partner.sid,
                 namespace=partner.namespace)
        sio.emit('answerer',
                 {'img': {'src': image_src,
                          'width': dialogue.picture.width,
                          'height': dialogue.picture.height},
                  'object': dialogue.object.to_json()},
                 room=sid,
                 namespace='/oracle')
    else:
        player.partner_sid = None
        oracle_queue.appendleft(player)


@sio.on('next oracle', namespace='/questioner1')
@sio.on('next oracle', namespace='/questioner2')
def find_oracle(sid):
    partner = False
    player = players[sid]

    if len(oracle_queue) > 0:
        partner = oracle_queue.pop()

    if partner:
        partner.partner_sid = player.sid
        player.partner_sid = partner.sid

        dialogue = db.start_dialogue()
        clients_dialogue[sid] = dialogue
        clients_dialogue[partner.sid] = dialogue
        image_src = ('https://msvocds.blob.core.windows.net/imgs/'
                     '{}.jpg').format(dialogue.picture.id)
        sio.emit('questioner',
                 {'img': {'src': image_src,
                          'width': dialogue.picture.width,
                          'height': dialogue.picture.height}},
                 room=sid,
                 namespace=player.namespace)
        sio.emit('answerer',
                 {'img': {'src': image_src,
                          'width': dialogue.picture.width,
                          'height': dialogue.picture.height},
                  'object': dialogue.object.to_json()},
                 room=partner.sid,
                 namespace=partner.namespace)
    else:
        player.partner_sid = None
        questioner_queue.appendleft(player)



@sio.on('connect', namespace='/oracle')
def connect(sid, re):
    players[sid] = Oracle(sid)


@sio.on('connect', namespace='/questioner1')
def q1_connect(sid, re):
    players[sid] = Questioner1(sid)


@sio.on('connect', namespace='/questioner2')
def q2_connect(sid, re):
    players[sid] = Questioner2(sid)


@sio.on('disconnect', namespace='/oracle')
@sio.on('disconnect', namespace='/questioner1')
@sio.on('disconnect', namespace='/questioner2')
def disconnect(sid):
    player = players[sid]
    if player.partner_sid is not None:
        partner = players[player.partner_sid]
        sio.emit('partner_disconnect',
                 '',
                 room=partner.sid,
                 namespace=partner.namespace)

        delete_game([sid, partner.sid])
        if partner.namespace == '/oracle':
            find_questioner(partner.sid)
        else:
            find_oracle(partner.sid)
    if player in oracle_queue:
        oracle_queue.remove(player)
    if player in questioner_queue:
        questioner_queue.remove(player)
    del players[sid]


def delete_game(sids):
    for sid in sids:
        if sid in players:
            player = players[sid]
            if player.partner_sid is not None:
                player.partner_sid = None
        if sid in clients_dialogue:
                del clients_dialogue[sid]
