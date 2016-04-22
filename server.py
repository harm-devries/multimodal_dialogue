import os
import random
import socketio
from collections import deque
from flask import Flask, render_template
from database.db_utils import DatabaseHelper
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
queue = deque()
players = {}  # indexed by socket id
clients_dialogue = {}  # Dialogue client is involved in


class Player():
    """Player wrapper."""

    def __init__(self, sid):
        self.sid = sid
        self.ban_sid = []
        self.partner_sid = None
        self.name = ''


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
    player = players[sid]
    partnerid = player.partner_sid
    delete_game([sid, partnerid])
    sio.emit('partner timeout', '',
             room=partnerid, namespace='/game')
    find_partner(partnerid)


@sio.on('newquestion', namespace='/game')
def new_question(sid, message):
    player = players[sid]
    dialogue = clients_dialogue[sid]
    dialogue.last_question_id = db.insert_question(dialogue.id, message)
    sio.emit('new question', message,
             room=player.partner_sid, namespace='/game')


@sio.on('new answer', namespace='/game')
def new_answer(sid, message):
    player = players[sid]
    dialogue = clients_dialogue[sid]
    db.insert_answer(dialogue.last_question_id, message)
    sio.emit('new answer', message,
             room=player.partner_sid, namespace='/game')


@sio.on('guess', namespace='/game')
def guess(sid):
    player = players[sid]
    dialogue = clients_dialogue[sid]
    objs = [obj.to_json() for obj in dialogue.picture.objects]
    sio.emit('all annotations', {'partner': False, 'objs': objs},
             room=sid, namespace='/game')
    sio.emit('all annotations', {'partner': True},
             room=player.partner_sid, namespace='/game')


@sio.on('guess annotation', namespace='/game')
def guess_annotation(sid, object_id):
    player = players[sid]
    dialogue = clients_dialogue[sid]
    db.insert_guess(dialogue.id, object_id)
    selected_obj = dialogue.object
    if selected_obj.object_id == object_id:
        db.update_score(player.name)
        db.update_score(players[player.partner_sid].name)
        sio.emit('correct annotation', {'partner': False,
                                        'object': selected_obj.to_json()},
                 room=sid, namespace='/game')
        sio.emit('correct annotation', {'partner': True,
                                        'object': selected_obj.to_json()},
                 room=player.partner_sid, namespace='/game')
    else:
        for obj in dialogue.picture.objects:
            if obj.object_id == object_id:
                guessed_obj = obj
        sio.emit('wrong annotation', {'partner': False,
                                      'object': selected_obj.to_json()},
                 room=sid, namespace='/game')
        sio.emit('wrong annotation', {'partner': True,
                                      'object': guessed_obj.to_json()},
                 room=player.partner_sid, namespace='/game')
    delete_game([player.sid, player.partner_sid])


@sio.on('next new', namespace='/game')
def find_new_player(sid):
    """Start game with new player. """
    player = players[sid]
    player.ban_sid = [player.previous_sid]
    find_partner(sid)


@sio.on('name', namespace='/game')
def set_name(sid, name):
    player = players[sid]
    player.name = name
    db.insert_name(name)


@sio.on('next', namespace='/game')
def find_partner(sid):
    partner = False
    player = players[sid]

    print 'before'
    for x in queue:
        print x.sid

    if len(queue) > 0:
        partner = queue.pop()

    # for p in banned_players:
    #     queue.appendleft(p)

    if partner:
        partner.partner_sid = player.sid
        player.partner_sid = partner.sid
        partner.ban_sid = []
        player.ban_sid = []
        role = (random.random() > 0.5)

        if role:
            dialogue = db.start_dialogue()
            clients_dialogue[sid] = dialogue
            clients_dialogue[partner.sid] = dialogue
            image_src = ('https://msvocds.blob.core.windows.net/imgs/'
                         '{}.jpg').format(dialogue.picture.id)
            sio.emit('questioner',
                     {'img': image_src},
                     room=partner.sid,
                     namespace='/game')
            sio.emit('answerer',
                     {'img': image_src,
                      'object': dialogue.object.to_json()},
                     room=sid,
                     namespace='/game')
        else:
            dialogue = db.start_dialogue()
            clients_dialogue[sid] = dialogue
            clients_dialogue[partner.sid] = dialogue
            image_src = ('https://msvocds.blob.core.windows.net/imgs/'
                         '{}.jpg').format(dialogue.picture.id)
            sio.emit('answerer',
                     {'img': image_src,
                      'object': dialogue.object.to_json()},
                     room=partner.sid,
                     namespace='/game')
            sio.emit('questioner',
                     {'img': image_src},
                     room=sid,
                     namespace='/game')
    else:
        player.partner_sid = None
        queue.appendleft(player)


@sio.on('connect', namespace='/game')
def connect(sid, re):
    players[sid] = Player(sid)


@sio.on('disconnect', namespace='/game')
def disconnect(sid):
    player = players[sid]
    if player.partner_sid is not None:
        partnerid = player.partner_sid
        sio.emit('partner_disconnect',
                 '',
                 room=partnerid,
                 namespace='/game')

        delete_game([sid, partnerid])
        find_partner(partnerid)
    del players[sid]


def delete_game(sids):
    for sid in sids:
        if sid in players:
            player = players[sid]
            if player.partner_sid is not None:
                player.previous_sid = player.partner_sid
                player.partner_sid = None
        if sid in clients_dialogue:
                del clients_dialogue[sid]
