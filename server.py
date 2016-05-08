import os
import socketio
import user_agents
import urlparse
from collections import deque
from flask import Flask, render_template, request
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


""" Database connection """
db = DatabaseHelper.from_postgresurl(
    os.environ['HEROKU_POSTGRESQL_SILVER_URL'])


@app.route('/')
def index():
    return render_template('index.html')


def check_browser(user_agent_string):
    browser_exclude_rule = ['MSIE', 'mobile', 'tablet']
    user_agent_obj = user_agents.parse(user_agent_string)
    browser_ok = True
    for rule in browser_exclude_rule:
        myrule = rule.strip()
        if myrule in ["mobile", "tablet", "touchcapable", "pc", "bot"]:
            if (myrule == "mobile" and user_agent_obj.is_mobile) or\
               (myrule == "tablet" and user_agent_obj.is_tablet) or\
               (myrule == "touchcapable" and user_agent_obj.is_touch_capable) or\
               (myrule == "pc" and user_agent_obj.is_pc) or\
               (myrule == "bot" and user_agent_obj.is_bot):
                browser_ok = False
        elif (myrule == "Safari" or myrule == "safari"):
            if "Chrome" in user_agent_string and "Safari" in user_agent_string:
                pass
            elif "Safari" in user_agent_string:
                browser_ok = False
        elif myrule in user_agent_string:
            browser_ok = False
    return browser_ok


@app.route('/oracle')
def oracle():
    if not check_browser(request.user_agent.string):
        # Handler for IE users if IE is not supported.
        msg = 'Your browswer is not supported.'
        return render_template('error.html', msg=msg)

    if not ('hitId' in request.args and 'assignmentId' in request.args):
        return render_template('error.html', msg='Missing mturk parameters.')

    if len(players) > 1000:
        msg = ('Sorry, there are currently'
               'more than 1000 players.')
        return render_template('error.html', title='Too many players',
                               msg=msg)

    accepted_hit = False
    if 'workerId' in request.args:
        accepted_hit = True
        for player in players.itervalues():
            if player.worker_id == request.args['workerId']:
                msg = ('You are allowed to play at most '
                       'one game at the same time.')
                return render_template('error.html', msg=msg)

    return render_template('oracle.html',
                           accepted_hit=accepted_hit)


@app.route('/questioner1')
def questioner1():
    if not check_browser(request.user_agent.string):
        # Handler for IE users if IE is not supported.
        msg = 'Your browswer is not supported.'
        return render_template('error.html', msg=msg)

    if not ('hitId' in request.args and 'assignmentId' in request.args):
        return render_template('error.html', msg='Missing mturk parameters.')

    if len(players) > 1000:
        msg = ('Sorry, there are currently'
               'more than 1000 players.')
        return render_template('error.html', title='Too many players',
                               msg=msg)

    accepted_hit = False
    if 'workerId' in request.args:
        accepted_hit = True
        for player in players.itervalues():
            if player.worker_id == request.args['workerId']:
                msg = ('You are allowed to play at most '
                       'one game at the same time.')
                return render_template('error.html', msg=msg)

    return render_template('questioner1.html',
                           accepted_hit=accepted_hit)


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
    partner = player.partner
    if partner.namespace == '/oracle':
        db.update_dialogue_status(player.dialogue.id, 'questioner_timeout')
    else:
        db.update_dialogue_status(player.dialogue.id, 'oracle_timeout')
    delete_game([player, partner])
    sio.emit('partner timeout', '',
             room=partner.sid, namespace=partner.namespace)
    if partner.role == 'Oracle':
        find_questioner(partner.sid)
    else:
        find_oracle(partner.sid)


@sio.on('newquestion', namespace='/questioner1')
def new_question(sid, message):
    player = players[sid]
    dialogue = player.dialogue
    dialogue.last_question_id = db.insert_question(dialogue.id, message)
    sio.emit('new question', message,
             room=player.partner.sid, namespace='/oracle')


@sio.on('new answer', namespace='/oracle')
def new_answer(sid, message):
    player = players[sid]
    partner = player.partner
    dialogue = player.dialogue
    db.insert_answer(dialogue.last_question_id, message)
    sio.emit('new answer', message,
             room=partner.sid, namespace=partner.namespace)


@sio.on('guess', namespace='/questioner1')
def guess(sid):
    player = players[sid]
    dialogue = player.dialogue
    objs = [obj.to_json() for obj in dialogue.picture.objects]
    sio.emit('all annotations', {'partner': False, 'objs': objs},
             room=sid, namespace=player.namespace)
    sio.emit('all annotations', {'partner': True},
             room=player.partner.sid, namespace='/oracle')


@sio.on('guess annotation', namespace='/questioner1')
def guess_annotation(sid, object_id):
    player = players[sid]
    dialogue = player.dialogue
    db.insert_guess(dialogue.id, object_id)
    selected_obj = dialogue.object
    if selected_obj.object_id == object_id:
        db.update_dialogue_status(dialogue.id, 'success')
        sio.emit('correct annotation', {'partner': False,
                                        'object': selected_obj.to_json()},
                 room=sid, namespace=player.namespace)
        sio.emit('correct annotation', {'partner': True,
                                        'object': selected_obj.to_json()},
                 room=player.partner.sid, namespace='/oracle')
    else:
        db.update_dialogue_status(dialogue.id, 'failure')
        for obj in dialogue.picture.objects:
            if obj.object_id == object_id:
                guessed_obj = obj
        sio.emit('wrong annotation', {'partner': False,
                                      'object': selected_obj.to_json()},
                 room=sid, namespace=player.namespace)
        sio.emit('wrong annotation', {'partner': True,
                                      'object': guessed_obj.to_json()},
                 room=player.partner.sid, namespace='/oracle')
    delete_game([player, player.partner])


@sio.on('next questioner', namespace='/oracle')
def find_questioner(sid):
    partner = False
    player = players[sid]

    if len(questioner_queue) > 0:
        partner = questioner_queue.pop()

    if partner:
        partner.partner = player
        player.partner = partner

        db.remove_from_queue(partner, 'dialogue')
        dialogue = db.start_dialogue(player.session_id, partner.session_id)
        partner.dialogue = dialogue
        player.dialogue = dialogue

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
        player.queue_id = db.insert_into_queue(player)
        oracle_queue.appendleft(player)


@sio.on('next oracle', namespace='/questioner1')
@sio.on('next oracle', namespace='/questioner2')
def find_oracle(sid):
    partner = False
    player = players[sid]

    if len(oracle_queue) > 0:
        partner = oracle_queue.pop()

    if partner:
        partner.partner = player
        player.partner = partner

        db.remove_from_queue(partner, 'dialogue')
        dialogue = db.start_dialogue(partner.session_id, player.session_id)
        partner.dialogue = dialogue
        player.dialogue = dialogue

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
        player.queue_id = db.insert_into_queue(player)
        questioner_queue.appendleft(player)


def get_ids(url):
    parsed = urlparse.urlparse(url)
    params = urlparse.parse_qs(parsed.query)
    return params['assignmentId'][0], params['hitId'][0], params['workerId'][0]


@sio.on('connect', namespace='/oracle')
def connect(sid, re):
    ass_id, hit_id, worker_id = get_ids(re['HTTP_REFERER'])
    ip = re['REMOTE_ADDR']
    player = Oracle(sid, ass_id, hit_id, worker_id, ip)
    player.session_id = db.insert_session(player)
    players[sid] = player


@sio.on('connect', namespace='/questioner1')
def q1_connect(sid, re):
    ass_id, hit_id, worker_id = get_ids(re['HTTP_REFERER'])
    ip = re['REMOTE_ADDR']
    player = Questioner1(sid, ass_id, hit_id, worker_id, ip)
    player.session_id = db.insert_session(player)
    players[sid] = player


@sio.on('connect', namespace='/questioner2')
def q2_connect(sid, re):
    ass_id, hit_id, worker_id = get_ids(re['HTTP_REFERER'])
    ip = re['REMOTE_ADDR']
    player = Questioner2(sid, ass_id, hit_id, worker_id, ip)
    player.session_id = db.insert_session(player)
    players[sid] = player


@sio.on('disconnect', namespace='/oracle')
@sio.on('disconnect', namespace='/questioner1')
@sio.on('disconnect', namespace='/questioner2')
def disconnect(sid):
    player = players[sid]
    """Four cases:
    1. Player is in involved in dialogue."""
    if player.partner is not None:
        partner = player.partner
        sio.emit('partner_disconnect',
                 '',
                 room=partner.sid,
                 namespace=partner.namespace)
        if partner.namespace == '/oracle':
            db.update_dialogue_status(player.dialogue.id,
                                      'questioner_disconnect')
        else:
            db.update_dialogue_status(player.dialogue.id,
                                      'oracle_disconnect')

        delete_game([player, partner])

        if partner.namespace == '/oracle':
            find_questioner(partner.sid)
        else:
            find_oracle(partner.sid)
    """2. Player is in oracle queue."""
    if player in oracle_queue:
        oracle_queue.remove(player)
        db.remove_from_queue(player, 'disconnect')
    """3. Player is in questioner queue"""
    if player in questioner_queue:
        questioner_queue.remove(player)
        db.remove_from_queue(player, 'disconnect')
    """4. Player did not start a game yet"""
    db.end_session(player.session_id)
    del players[sid]


def delete_game(players):
    """Remove dialogues"""
    for player in players:
        player.partner = None
        player.dialogue = None
