import datetime
import json
import os
import random
import socketio
import urlparse
import user_agents
from collections import deque
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from database.db_utils import (get_dialogues, get_dialogue_stats,
                               get_dialogue_guess, get_dialogue_object,
                               get_dialogue_conversation, get_dialogue_info,
                               get_workers, get_worker,
                               insert_question, insert_answer, insert_guess,
                               insert_session, end_session, update_session,
                               update_dialogue_status, start_dialogue,
                               remove_from_queue, insert_into_queue,
                               get_worker_status, get_assignment_stats,
                               get_one_worker_status, update_one_worker_status,
                               assignment_completed, is_worker_playing, get_ongoing_workers,
                               report_answer)
from worker import (check_qualified, check_blocked, check_assignment_completed,
                    pay_questioner_bonus, pay_oracle_bonus)
from players import QualifyOracle, Oracle, QualifyQuestioner, Questioner


# set this to 'threading', 'eventlet', or 'gevent'
async_mode = 'eventlet'

if async_mode == 'gevent':
    from gevent import monkey
    monkey.patch_all()
if async_mode == 'eventlet':
    import eventlet
    eventlet.monkey_patch()

sio = socketio.Server(logger=True, engineio_logger=True, async_mode=async_mode, ping_interval=20)
app = Flask(__name__)
app.wsgi_app = socketio.Middleware(sio, app.wsgi_app)
app.config['SECRET_KEY'] = 'spywithmylittleeye!'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['HEROKU_POSTGRESQL_SILVER_URL']
db = SQLAlchemy(app)
engine = db.engine
thread = None

""" Dictionaries for dialogue info that remains in RAM """
q_oracle_queue = deque()
q_questioner_queue = deque()

oracle_queue = deque()
questioner_queue = deque()

players = {}  # indexed by socket id
dialogues = {}  # indexed by dialogue_id
auth = HTTPBasicAuth()





@auth.get_password
def get_pw(username):
    return "multimodal"


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



@sio.on('show dialogue')
def update_answer(sid, msg):
    player, partner, dialogue = get_dialogue_and_players(sid)
    with engine.begin() as conn:
        ans = {'Yes': 'Yes', 'No': 'No', 'Not applicable': 'N/A'}[msg['new_msg']]
        insert_answer(conn, dialogue.question_ids[msg['round']], ans)
    sio.emit('update answer', msg, room=partner.sid, namespace=partner.namespace)



@app.route('/fix_mistake')
def q_oracle():
    if not check_browser(request.user_agent.string):
        # Handler for IE users if IE is not supported.
        msg = 'Your browser is not supported.'
        return render_template('error.html', msg=msg)

    if not ('hitId' in request.args and
            'assignmentId' in request.args):
        return render_template('error.html', title='Oracle - ',
                               msg='Missing mturk parameters.')

    assignment_id = request.args['assignmentId']

    if len(players) > 1000:
        msg = ('Sorry, there are currently'
               'more than 1000 players.')
        return render_template('error.html', title='Oracle - ',
                               msg=msg)

    turk_submit_to = 'https://workersandbox.mturk.com'
    if 'turkSubmitTo' in request.args:
        turk_submit_to = request.args['turkSubmitTo']

    accepted_hit = False


    global thread
    #if thread is None:
    #    thread = sio.start_background_task(check_for_timeouts)


    id=46206
    question_id = 181134

    with engine.begin() as conn:
        (picture_id, width, height, status,
         oracle_id, questioner_id, time) = get_dialogue_info(conn, id)

        if picture_id is None:
            return render_template('error.html', msg='Dialogue not found.')

        image = ('https://msvocds.blob.core.windows.net/imgs/{}.jpg').format(picture_id)
        guess = get_dialogue_guess(conn, id)
        obj = get_dialogue_object(conn, id)
        objs = [obj.to_json()]
        if guess is not None and guess.object_id != obj.object_id:
            objs.append(guess.to_json())
        qas = get_dialogue_conversation(conn, id)
        qas = [_qas for _qas in reversed(qas)]

    for i, x in enumerate(qas):
        if x.question_id == question_id:
            question_index = i
            break
    else:
        question_index = 0

    print("coucou")
    question1 = {}
    question1["dialogue_id"] = id
    question1["question_id"] = question_id
    question1["question_index"] = question_index
    question1["question"] = "is it left most in the pic"
    question1["qas"] = qas
    question1["img"] = image


    questions_to_fix = [question1]

    return render_template('mistakes.html',  title='Mistake - ', mistakes=questions_to_fix)




@app.route('/dialogues')
@auth.login_required
def getdialogues():
    return render_template('dialogues.html', dialogues=get_dialogues(engine))


@app.route('/dialogue_stats/<mode>')
@auth.login_required
def dialogue_stats(mode):
    print (mode)
    counts, avg_seconds, avg_questions = get_dialogue_stats(engine, mode=mode)
    return render_template('dialogue_stats.html', counts=counts,
                           avg_questions=avg_questions,
                           avg_seconds=avg_seconds)


@app.route('/dialogue/<id>')
@auth.login_required
def show_dialogue(id):
    conn = engine.connect()
    (picture_id, width, height, status,
     oracle_id, questioner_id, time) = get_dialogue_info(conn, id)

    if picture_id is None:
        return render_template('error.html', msg='Dialogue not found.')

    image = ('https://msvocds.blob.core.windows.net/imgs/'
             '{}.jpg').format(picture_id)

    print(image)

    guess = get_dialogue_guess(conn, id)
    obj = get_dialogue_object(conn, id)
    objs = [obj.to_json()]
    if guess is not None and guess.object_id != obj.object_id:
        objs.append(guess.to_json())
    qas = get_dialogue_conversation(conn, id)
    conn.close()

    return render_template('dialogue.html',
                           status=status,
                           oracle_id=oracle_id,
                           questioner_id=questioner_id,
                           time=time,
                           qas=qas,
                           img={'src': image, 'width': width,
                                'height': height},
                           obj=json.dumps(objs))


@app.route('/workers')
@auth.login_required
def workers():
    conn = engine.connect()
    workers = get_workers(conn)
    conn.close()
    return render_template('workers.html', workers=workers)


def render_worker(id):
    with engine.begin() as conn:
        worker_dialogues = get_worker(conn, id)
        status = get_one_worker_status(conn, id)

        ongoing_worker = is_worker_playing(conn, id)

        status["playing"] = ongoing_worker.is_playing
        status["role"] = ongoing_worker.role
        status["socket_db"] = ongoing_worker.socket_id
        status["socket_io"] = 0

        for sid, player in players.iteritems():
            if player.worker_id == id:
                status["socket_io"] = sid
                break

    return render_template('worker.html', dialogues=worker_dialogues, worker=status)


@app.route('/worker/<id>')
@auth.login_required
def worker(id):
    return render_worker(id)



@auth.login_required
@app.route('/worker/<id>/remove_socket', methods=['POST'])
def one_worker_remove_socket(id):
    sid_to_remove = request.form['text_socket_io']
    if sid_to_remove in players:
        del players[sid_to_remove]

    return render_worker(id)


def render_stats_io_error():
    # retrieve workers that are currently playing a dialogue
    with engine.begin() as conn:
        ongoing_workers = get_ongoing_workers(conn)

    # helper to get sid from worker id
    def get_sid(worker_id):
        for sid, w in players.iteritems():
            if w.worker_id == worker_id:
                return sid
        return 0

    # list all the current open sockets
    workers = []
    for socket_id, player in players.iteritems():
        one_worker = dict()
        one_worker["id"] = player.worker_id
        one_worker["playing"] = player.worker_id in ongoing_workers
        one_worker["role"] = ongoing_workers[player.worker_id].role
        one_worker["socket_db"] = ongoing_workers[player.worker_id].socket_id
        one_worker["socket_io"] = get_sid(player.worker_id)
        workers.append(one_worker)

    return render_template('socket_io.html', workers=workers)


@auth.login_required
@app.route('/stats/io_error')
def stats_io_error():
    return render_stats_io_error()


@auth.login_required
@app.route('/stats/io_error', methods=['POST'])
def stats_io_error_update():
    # get the checkbox with the sid to remove
    sid_to_remove = request.form.getlist('check')
    for sid in sid_to_remove:
        del players[sid]
    return render_stats_io_error()


@app.route('/stats')
def stats():
    msg = '<br />'.join([', '.join([sid, str(sio.eio.sockets[sid].closed), str(sio.eio.sockets[sid].upgraded), str(sio.eio.sockets[sid].connected), str(sio.eio.sockets[sid].last_ping)]) for sid in sio.eio.sockets.keys()])
    return render_template('error.html', msg=msg)


def get_dialogue_and_players(sid):
    player = players[sid]
    partner = player.partner
    dialogue = dialogues[player.dialogue_id]
    return player, partner, dialogue



@sio.on('new answer', namespace='/q_oracle')
@sio.on('new answer', namespace='/oracle')
def new_answer(sid, message):
    player, partner, dialogue = get_dialogue_and_players(sid)

    with engine.begin() as conn:
        insert_answer(conn, dialogue.question_ids[-1], message)

    dialogue.turn = 'questioner'
    dialogue.deadline = datetime.datetime.now() + datetime.timedelta(seconds=90)

    sio.emit('new answer', message,
             room=partner.sid, namespace=partner.namespace)


@sio.on('update answer', namespace='/q_oracle')
@sio.on('update answer', namespace='/oracle')
def update_answer(sid, msg):
    player, partner, dialogue = get_dialogue_and_players(sid)
    with engine.begin() as conn:
        ans = {'Yes': 'Yes', 'No': 'No', 'Not applicable': 'N/A'}[msg['new_msg']]
        insert_answer(conn, dialogue.question_ids[msg['round']], ans)
    sio.emit('update answer', msg, room=partner.sid, namespace=partner.namespace)




def get_hit_info(url):
    par = urlparse.parse_qs(urlparse.urlparse(url).query)
    return par['hitId'][0], par['assignmentId'][0], par['workerId'][0]


def connect_player(_Player, sid, response):

    # Retrieve info from HTTP header
    ip = response['REMOTE_ADDR']
    hit_id, assignment_id, worker_id = get_hit_info(response['HTTP_REFERER'])

    # Create player
    player = _Player(sid, hit_id, assignment_id, worker_id, ip)

    # Insert player in the database
    with engine.begin() as conn:
        player.session_id = insert_session(conn, player)

    players[sid] = player
    print('add: ' + str(sid))



@sio.on('update session', namespace='/oracle')
@sio.on('update session', namespace='/q_questioner')
@sio.on('update session', namespace='/questioner')
def up_session(sid, msg):
    player = players[sid]
    player.assignment_id = msg['assignmentId']
    player.hit_id = msg['hitId']
    player.worker_id = msg['workerId']

    with engine.begin() as conn:
        update_session(conn, player)



@sio.on('disconnect', namespace='/oracle')
@sio.on('disconnect', namespace='/q_oracle')
@sio.on('disconnect', namespace='/questioner')
@sio.on('disconnect', namespace='/q_questioner')
def disconnect(sid):
    if sid in players:
        player = players[sid]





@app.errorhandler(500)
def internal_error(error):
    print (error)
    return "500 error"

#if async_mode == 'eventlet':
#    eventlet.wsgi.server(eventlet.listen(('', int(os.environ['PORT']))), app)
