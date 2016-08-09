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

sio = socketio.Server(logger=True, engineio_logger=True, async_mode=async_mode, ping_timeout=25)
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


def time_out(dialogue):
    conn = engine.connect()

    oracle = players[dialogue.oracle_sid] if dialogue.oracle_sid in players else None
    questioner = players[dialogue.questioner_sid] if dialogue.questioner_sid in players else None

    print("time out")
    print("oracle    : " + oracle.worker_id     + " \t dialogue.sid: " + str(dialogue.oracle_sid))
    print("questioner: " + questioner.worker_id + " \t dialogue.sid: " + str(dialogue.questioner_sid))

    if dialogue.turn == 'oracle':
        # Oracle time out
        update_dialogue_status(conn, dialogue.id, 'oracle_timeout')
        delete_game([oracle, questioner])
        sio.emit('timeout', '',
                 room=oracle.sid, namespace=oracle.namespace)
        sio.emit('partner timeout', '',
                 room=questioner.sid, namespace=questioner.namespace)
        if questioner.role == 'Questioner':
            find_normal_oracle(questioner.sid)
        else:
            find_qualification_oracle(questioner.sid)
        check_blocked(conn, oracle)
    else:
        # Questioner timeout
        update_dialogue_status(conn, dialogue.id, 'questioner_timeout')
        delete_game([oracle, questioner])
        sio.emit('timeout', '',
                 room=questioner.sid, namespace=questioner.namespace)
        sio.emit('partner timeout', '',
                 room=oracle.sid, namespace=oracle.namespace)
        if oracle.role == 'Oracle':
            find_normal_questioner(oracle.sid)
        else:
            find_qualification_questioner(oracle.sid)
        check_blocked(conn, questioner)
    conn.close()

"""Background process checking for dialogues that time out."""
def check_for_timeouts():
    while True:
        sio.sleep(0.01)  # return control so other threads can execute
        keys = dialogues.keys()
        for key in keys:
            if key in dialogues:
                dialogue = dialogues[key]
                if datetime.datetime.now() > dialogue.deadline:
                    time_out(dialogue)
            sio.sleep(0.01)


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


@app.route('/qualify_oracle')
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
    nr_success, nr_failure, nr_disconnects = 0, 0, 0
    if 'workerId' in request.args:
        worker_id = request.args['workerId']
        accepted_hit = True
        conn = engine.connect()
        worker_status = get_worker_status(conn, worker_id)
        if worker_status == 'blocked':
            return render_template('error.html', title='Oracle - ',
                                   msg='Your account is currently blocked, probably because you\'ve made too many mistakes or disconnected too many times while completing the HIT. Contact Harm de Vries at guesswhat.mturk@gmail.com for more information about your account (include your worker id).')

        if worker_status == 'qualified':
            return render_template('error.html', title='Oracle - ',
                                   msg='You are already qualified as an oracle. Please search for Guesswhat?! HIT with [QUALIFIED ONLY] in the title.')

        stats = get_assignment_stats(conn, assignment_id, questioner=False)
        nr_success, nr_failure = stats['success'], stats['failure'] + stats['oracle_reported']
        nr_disconnects = stats['oracle_disconnect'] + stats['oracle_timeout']

        for player in players.itervalues():
            if player.worker_id == worker_id and player.role == 'QualifyQuestioner':
                msg = ('You are not allowed to play '
                       'multiple games at the same time.')
                return render_template('error.html', title='Oracle - ',
                                       msg=msg)

    global thread
    if thread is None:
        thread = sio.start_background_task(check_for_timeouts)

    return render_template('oracle.html',
                           title='Oracle - ',
                           accepted_hit=accepted_hit,
                           assignmentId=assignment_id,
                           success=nr_success,
                           failure=nr_failure,
                           disconnect=nr_disconnects,
                           turkSubmitTo=turk_submit_to,
                           namespace='/q_oracle')


@app.route('/oracle')
def oracle():
    if not check_browser(request.user_agent.string):
        # Handler for IE users if IE is not supported.
        msg = 'Your browswer is not supported.'
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
    nr_success, nr_failure, nr_disconnects = 0, 0, 0
    if 'workerId' in request.args:
        worker_id = request.args['workerId']
        accepted_hit = True
        conn = engine.connect()
        worker_status = get_worker_status(conn, worker_id, questioner=False)
        if worker_status == 'blocked':
            return render_template('error.html', title='Oracle - ',
                                   msg='Your account is currently blocked, probably because you\'ve made too many mistakes or disconnected too many times while completing the HIT. Contact Harm de Vries - guesswhat.mturk@gmail.com - for more information.')

        if worker_status is None or worker_status == 'default':
            return render_template('error.html', title='Oracle - ',
                                   msg='You are not qualified yet to play Guesswhat?!. Please search for GuessWhat?! HIT without [QUALIFIED ONLY] in the title.')

        if assignment_completed(conn, assignment_id):
            return render_template('error.html', title='Questioner - ',
                                   msg='You have already completed this assignment.')

        stats = get_assignment_stats(conn, assignment_id, questioner=False)
        nr_success, nr_failure = stats['success'], stats['failure'] + stats['oracle_reported']
        nr_disconnects = stats['oracle_disconnect'] + stats['oracle_timeout']

        if (nr_failure + nr_disconnects) > 3:
            return render_template('error.html', title='Oracle - ',
                                   msg='You have made too many mistakes to successfully complete this assignment. Please return accepted HIT. ')

        for player in players.itervalues():
            if player.worker_id == request.args['workerId'] and player.role == 'Questioner':
                msg = ('You are allowed to play at most '
                       'one game at the same time.')
                return render_template('error.html', title='Oracle - ',
                                       msg=msg)
    global thread
    if thread is None or not thread.is_alive():
        thread = sio.start_background_task(check_for_timeouts)

    return render_template('oracle.html',
                           title='Oracle - ',
                           success=nr_success,
                           failure=nr_failure,
                           disconnect=nr_disconnects,
                           accepted_hit=accepted_hit,
                           assignmentId=assignment_id,
                           turkSubmitTo=turk_submit_to,
                           namespace='/oracle')


@app.route('/qualify_questioner')
def q_questioner():
    if not check_browser(request.user_agent.string):
        # Handler for IE users if IE is not supported.
        msg = 'Your browswer is not supported.'
        return render_template('error.html', title='Questioner - ', msg=msg)

    if not ('hitId' in request.args and
            'assignmentId' in request.args):
        return render_template('error.html', title='Questioner - ',
                               msg='Missing mturk parameters.')

    if len(players) > 1000:
        msg = ('Sorry, there are currently'
               'more than 1000 players.')
        return render_template('error.html', title='Questioner - ',
                               msg=msg)

    assignment_id = request.args['assignmentId']

    turk_submit_to = 'https://workersandbox.mturk.com'
    if 'turkSubmitTo' in request.args:
        turk_submit_to = request.args['turkSubmitTo']

    accepted_hit = False
    nr_success, nr_failure, nr_disconnects = 0, 0, 0

    if 'workerId' in request.args:
        worker_id = request.args['workerId']
        accepted_hit = True
        conn = engine.connect()
        worker_status = get_worker_status(conn, worker_id, questioner=True)
        if worker_status == 'blocked':
            return render_template('error.html', title='Questioner - ',
                                   msg='Your account is currently blocked, probably because you\'ve made too many mistakes or disconnected too many times while completing the HIT. Contact Harm de Vries - guesswhat.mturk@gmail.com - for more information.')

        if worker_status == 'qualified':
            return render_template('error.html', title='Questioner - ',
                                   msg='You are already qualified as a questioner. Please search for GuessWhat?! HIT with [QUALIFIED ONLY] in the title.')

        stats = get_assignment_stats(conn, assignment_id, questioner=True)
        nr_success, nr_failure = stats['success'], stats['failure'] + stats['oracle_reported']
        nr_disconnects = stats['questioner_disconnect'] + stats['questioner_timeout']
        for player in players.itervalues():
            if player.worker_id == request.args['workerId'] and player.role == 'QualifyOracle':
                msg = ('You are allowed to play at most '
                       'one game at the same time.')
                return render_template('error.html', title='Questioner - ',
                                       msg=msg)

    global thread
    if thread is None or not thread.is_alive():
        thread = sio.start_background_task(check_for_timeouts)


    return render_template('questioner.html',
                           title='Questioner - ',
                           assignmentId=assignment_id,
                           accepted_hit=accepted_hit,
                           success=nr_success,
                           failure=nr_failure,
                           disconnect=nr_disconnects,
                           turkSubmitTo=turk_submit_to,
                           namespace='/q_questioner')


@app.route('/questioner')
def questioner():
    if not check_browser(request.user_agent.string):
        # Handler for IE users if IE is not supported.
        msg = 'Your browswer is not supported.'
        return render_template('error.html', title='Questioner - ', msg=msg)

    if not ('hitId' in request.args and
            'assignmentId' in request.args):
        return render_template('error.html', title='Questioner - ',
                               msg='Missing mturk parameters.')

    assignment_id = request.args['assignmentId']

    if len(players) > 1000:
        msg = ('Sorry, there are currently'
               'more than 1000 players.')
        return render_template('error.html', title='Questioner - ',
                               msg=msg)

    turk_submit_to = 'https://workersandbox.mturk.com'
    if 'turkSubmitTo' in request.args:
        turk_submit_to = request.args['turkSubmitTo']

    accepted_hit = False
    nr_success, nr_failure, nr_disconnects = 0, 0, 0
    if 'workerId' in request.args:
        accepted_hit = True
        worker_id = request.args['workerId']

        conn = engine.connect()
        worker_status = get_worker_status(conn, worker_id, questioner=True)
        if worker_status == 'blocked':
            return render_template('error.html', title='Questioner - ',
                                   msg='Your account is currently blocked, probably because you\'ve made too many mistakes or disconnected too many times while completing the HIT. Contact Harm de Vries - guesswhat.mturk@gmail.com - for more information.')

        if worker_status is None or worker_status == 'default':
            return render_template('error.html', title='Questioner - ',
                                   msg='You are not qualified yet to play Guesswhat?!. Please search for GuessWhat?! HIT without [QUALIFIED ONLY] in the title.')
        if assignment_completed(conn, assignment_id):
            return render_template('error.html', title='Questioner - ',
                                   msg='You have already completed this assignment.')

        stats = get_assignment_stats(conn, assignment_id, questioner=True)
        nr_success, nr_failure = stats['success'], stats['failure'] + stats['oracle_reported']
        nr_disconnects = stats['questioner_disconnect'] + stats['questioner_timeout']

        if (nr_failure + nr_disconnects) > 3:
            return render_template('error.html', title='Questioner - ',
                                   msg='You have made too many mistakes to successfully complete this assignment. Please return accepted HIT. ')

        for player in players.itervalues():
            if player.worker_id == request.args['workerId'] and player.role == 'Oracle':
                msg = ('You are allowed to play at most '
                       'one game at the same time.')
                return render_template('error.html', title='Questioner - ',
                                       msg=msg)

    global thread
    if thread is None or not thread.is_alive():
        thread = sio.start_background_task(check_for_timeouts)

    return render_template('questioner.html',
                           title='Questioner - ',
                           success=nr_success,
                           failure=nr_failure,
                           disconnect=nr_disconnects,
                           accepted_hit=accepted_hit,
                           assignmentId=assignment_id,
                           turkSubmitTo=turk_submit_to,
                           namespace='/questioner')


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
@app.route('/worker/<id>/questioner_status', methods=['POST'])
def one_worker_questioner_status(id):
    with engine.begin() as conn:
        update_one_worker_status(conn, id, "questioner_status", request.form['questioner_status'])
    return render_worker(id)


@auth.login_required
@app.route('/worker/<id>/oracle_status', methods=['POST'])
def one_worker_oracle_status(id):
    with engine.begin() as conn:
        update_one_worker_status(conn, id, "oracle_status", request.form['oracle_status'])
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
    msg = '<br />'.join([', '.join([sid, players[sid].worker_id, sio.eio.sockets[sid].closed, sio.eio.sockets[sid].upgraded, sio.eio.sockets[sid].connected, sio.eio.sockets[sid].last_ping]) for sid in sio.eio.sockets.keys()])
    return render_template('error.html', msg=msg)


def get_dialogue_and_players(sid):
    player = players[sid]
    partner = player.partner
    dialogue = dialogues[player.dialogue_id]
    return player, partner, dialogue


@sio.on('report oracle', namespace='/q_questioner')
@sio.on('report oracle', namespace='/questioner')
def report_oracle(sid, reason):
    player, partner, dialogue = get_dialogue_and_players(sid)

    with engine.begin() as conn:
        update_dialogue_status(conn, dialogue.id, 'oracle_reported',
                               reason=reason)

    delete_game([player, partner])
    sio.emit('reported', '', room=partner.sid, namespace=partner.namespace)
    if partner.role == "QualifyOracle":
        find_qualification_questioner(partner.sid)
        find_qualification_oracle(player.sid)
    else:
        find_normal_questioner(partner.sid)
        find_normal_oracle(player.sid)


@sio.on('report oracle endgame', namespace='/q_questioner')
@sio.on('report oracle endgame', namespace='/questioner')
def report_oracle_end(sid, data):

    # Retrieve json data
    ranks_to_report = data["id_to_report"]
    dialogue_id = data["dialogue_id"]
    comments = data["comments"]

    # store reported data in db
    with engine.begin() as conn:
        report_answer(conn, dialogue_id=dialogue_id, ranks=ranks_to_report)
        update_dialogue_status(conn, dialogue_id, 'oracle_reported', reason=comments)


@sio.on('report questioner', namespace='/q_oracle')
@sio.on('report questioner', namespace='/oracle')
def report_questioner(sid, reason):
    player, partner, dialogue = get_dialogue_and_players(sid)

    with engine.begin() as conn:
        update_dialogue_status(conn, dialogue.id, 'questioner_reported',
                               reason=reason)
    delete_game([player, partner])
    sio.emit('reported', '', room=partner.sid, namespace=partner.namespace)
    if partner.role == "QualifyQuestioner":
        find_qualification_oracle(partner.sid)
        find_qualification_questioner(player.sid)
    else:
        find_normal_oracle(partner.sid)
        find_normal_questioner(player.sid)



@sio.on('newquestion', namespace='/q_questioner')
@sio.on('newquestion', namespace='/questioner')
def new_question(sid, message):
    player, partner, dialogue = get_dialogue_and_players(sid)

    with engine.begin() as conn:
        dialogue.question_ids.append(
            insert_question(conn, dialogue.id, message))

    dialogue.turn = 'oracle'
    dialogue.deadline = datetime.datetime.now() + datetime.timedelta(seconds=30)

    sio.emit('new question', message,
             room=player.partner.sid, namespace=partner.namespace)


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



@sio.on('guess', namespace='/q_questioner')
@sio.on('guess', namespace='/questioner')
def guess(sid):
    player = players[sid]
    dialogue = dialogues[player.dialogue_id]
    dialogue.turn = 'questioner'
    dialogue.deadline = datetime.datetime.now() + datetime.timedelta(seconds=30)
    objs = [obj.to_json() for obj in dialogue.picture.objects]
    sio.emit('all annotations', {'objs': objs},
             room=sid, namespace=player.namespace)
    sio.emit('start guessing', '',
             room=player.partner.sid, namespace=player.partner.namespace)


@sio.on('guess annotation', namespace='/q_questioner')
def guess_annotation(sid, object_id):
    player = players[sid]
    dialogue = dialogues[player.dialogue_id]
    conn = engine.connect()
    insert_guess(conn, dialogue.id, object_id)
    selected_obj = dialogue.object
    if selected_obj.object_id == object_id:
        update_dialogue_status(conn, dialogue.id, 'success')

        stats, finished_flag = check_qualified(conn, player)
        sio.emit('correct annotation', {'object': selected_obj.to_json(),
                                        'stats': stats,
                                        'finished': finished_flag,
                                        'qualified': False},
                 room=sid, namespace=player.namespace)
        stats, finished_flag = check_qualified(conn, player.partner)
        sio.emit('correct annotation', {'object': selected_obj.to_json(),
                                        'stats': stats,
                                        'finished': finished_flag,
                                        'qualified': False},
                 room=player.partner.sid, namespace=player.partner.namespace)
    else:
        update_dialogue_status(conn, dialogue.id, 'failure')
        for obj in dialogue.picture.objects:
            if obj.object_id == object_id:
                guessed_obj = obj
        stats, blocked = check_blocked(conn, player)
        sio.emit('wrong annotation', {'object': selected_obj.to_json(),
                                      'stats': stats,
                                      'blocked': blocked,
                                      'qualified': False},
                 room=sid, namespace=player.namespace)
        stats, blocked = check_blocked(conn, player.partner)
        sio.emit('wrong annotation', {'object': guessed_obj.to_json(),
                                      'stats': stats,
                                      'blocked': blocked,
                                      'qualified': False},
                 room=player.partner.sid, namespace=player.partner.namespace)
    delete_game([player, player.partner])
    conn.close()


@sio.on('guess annotation', namespace='/questioner')
def guess_annotation2(sid, object_id):
    player = players[sid]
    dialogue = dialogues[player.dialogue_id]
    conn = engine.connect()
    insert_guess(conn, dialogue.id, object_id)
    selected_obj = dialogue.object
    if selected_obj.object_id == object_id:
        update_dialogue_status(conn, dialogue.id, 'success')
        stats, finished_flag1 = check_assignment_completed(conn, player)
        sio.emit('correct annotation', {'object': selected_obj.to_json(),
                                        'stats': stats,
                                        'finished': finished_flag1,
                                        'qualified': True},
                 room=sid, namespace=player.namespace)

        stats = get_assignment_stats(conn, player.partner.worker_id,
                                     questioner=False)

        stats, finished_flag2 = check_assignment_completed(conn, player.partner)
        sio.emit('correct annotation', {'object': selected_obj.to_json(),
                                        'stats': stats,
                                        'finished': finished_flag2,
                                        'qualified': True},
                 room=player.partner.sid, namespace='/oracle')
        if finished_flag1:
            pay_questioner_bonus(conn, player)
        if finished_flag2:
            pay_oracle_bonus(conn, player.partner)
    else:
        update_dialogue_status(conn, dialogue.id, 'failure')
        for obj in dialogue.picture.objects:
            if obj.object_id == object_id:
                guessed_obj = obj
        stats = get_assignment_stats(conn, player.assignment_id,
                                     questioner=True)
        blocked = False
        if (stats['failure'] + stats['questioner_disconnect'] + stats['questioner_timeout'] + stats['oracle_reported']) > 3:
            blocked = True
        sio.emit('wrong annotation', {'object': selected_obj.to_json(),
                                      'stats': stats,
                                      'blocked': blocked,
                                      'qualified': True},
                 room=sid, namespace=player.namespace)
        stats = get_assignment_stats(conn, player.partner.assignment_id,
                                     questioner=False)
        blocked = False
        if (stats['failure'] + stats['oracle_disconnect'] + stats['oracle_timeout'] + stats['oracle_reported']) > 3:
            blocked = True
        sio.emit('wrong annotation', {'object': guessed_obj.to_json(),
                                      'stats': stats,
                                      'blocked': blocked,
                                      'qualified': True},
                 room=player.partner.sid, namespace='/oracle')
    delete_game([player, player.partner])
    conn.close()


def get_difficulty(player):
    sample = random.random()
    if player.is_qualified():
        if sample > 0.3:
            difficulty = 2
        else:
            difficulty = 1
    else:
        if sample > 0.3:
            difficulty = 1
        else:
            difficulty = 2

    return difficulty


@sio.on('next questioner', namespace='/q_oracle')
def find_qualification_questioner(sid):
    find_player(sid, _player_queue=q_oracle_queue, _partner_queue=q_questioner_queue, mode='qualification')


@sio.on('next questioner', namespace='/oracle')
def find_normal_questioner(sid):
    find_player(sid, _player_queue=oracle_queue, _partner_queue=questioner_queue, mode='normal')


@sio.on('next oracle', namespace='/q_questioner')
def find_qualification_oracle(sid):
    find_player(sid, _player_queue=q_questioner_queue, _partner_queue=q_oracle_queue, mode='qualification')


@sio.on('next oracle', namespace='/questioner')
def find_normal_oracle(sid):
    find_player(sid, _player_queue=questioner_queue, _partner_queue=oracle_queue, mode='normal')


def find_player(sid, _player_queue, _partner_queue, mode):
    # Retrieve players by socket id
    player = players[sid]

    # If a partner is available, start a new dialogue with the current player
    if len(_partner_queue) > 0:

        # remove partner from queue
        with engine.begin() as conn:
            partner = _partner_queue.pop()
            remove_from_queue(conn, partner, 'dialogue')

        # Provide each other partners
        partner.partner = player
        player.partner = partner

        instantiate_dialogue(player=player, partner=partner, mode=mode)

    # Otherwise, queue the player
    else:
        player.partner_sid = None

        with engine.begin() as conn:
            player.queue_id = insert_into_queue(conn, player)

        _player_queue.appendleft(player)


def instantiate_dialogue(player, partner, mode):
    # define roles
    oracle_ping, questioner_ping = False, False
    if player.is_questioner():
        _questioner = player
        _oracle = partner
        oracle_ping = True
    else:
        _questioner = partner
        _oracle = player
        questioner_ping = True

    # Instantiate a new dialogue in the db
    with engine.begin() as conn:
        dialogue = start_dialogue(conn, difficulty=get_difficulty(player), mode=mode,
                                  questioner_session_id=_questioner.session_id,
                                  oracle_session_id=_oracle.session_id)

    # Store dialogue id
    dialogues[dialogue.id] = dialogue
    partner.dialogue_id = dialogue.id
    player.dialogue_id = dialogue.id

    # provide sid
    dialogue.oracle_sid = _oracle.sid
    dialogue.questioner_sid = _questioner.sid

    # Create json msg for both questioner/oracle
    image_src = ('https://msvocds.blob.core.windows.net/imgs/{}.jpg').format(dialogue.picture.id)

    sio.emit('questioner',
             {'img': {'src': image_src,
                      'width': dialogue.picture.width,
                      'height': dialogue.picture.height},
              'dialogue_id': dialogue.id,
              'ping': questioner_ping},
             room=_questioner.sid,
             namespace=_questioner.namespace)
    sio.emit('answerer',
             {'img': {'src': image_src,
                      'width': dialogue.picture.width,
                      'height': dialogue.picture.height},
              'object': dialogue.object.to_json(),
              'dialogue_id': dialogue.id,
              'ping': oracle_ping},
             room=_oracle.sid,
             namespace=_oracle.namespace,
             )


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

@sio.on('connect', namespace='/q_oracle')
def q_oracle_connect(sid, re):
    connect_player(QualifyOracle, sid, re)

@sio.on('connect', namespace='/oracle')
def oracle_connect(sid, re):
    connect_player(Oracle, sid, re)

@sio.on('connect', namespace='/questioner')
def questioner_connect(sid, re):
    connect_player(Questioner, sid, re)

@sio.on('connect', namespace='/q_questioner')
def q_questioner_connect(sid, re):
    connect_player(QualifyQuestioner, sid, re)



@sio.on('update session', namespace='/q_oracle')
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

        with engine.begin() as conn:
            """Four cases:
            1. Player is in involved in dialogue."""
            if player.partner is not None:
                dialogue = dialogues[player.dialogue_id]
                partner = player.partner
                sio.emit('partner_disconnect',
                         '',
                         room=partner.sid,
                         namespace=partner.namespace)
                if partner.role in ['Oracle', 'QualifyOracle']:
                    update_dialogue_status(conn, dialogue.id,
                                           'questioner_disconnect')
                else:
                    update_dialogue_status(conn, dialogue.id,
                                           'oracle_disconnect')
                if player.role == 'QualifyOracle' or player.role == 'QualifyQuestioner':
                    check_blocked(conn, player)
                delete_game([player, partner])

                if partner.role == 'Oracle':
                    find_normal_questioner(partner.sid)
                elif partner.role == 'QualifyOracle':
                    find_qualification_questioner(partner.sid)
                elif partner.role == 'QualifyQuestioner':
                    find_qualification_oracle(partner.sid)
                else:
                    find_normal_oracle(partner.sid)
            """2. Player is in oracle queue."""
            if player in oracle_queue:
                oracle_queue.remove(player)
                remove_from_queue(conn, player, 'disconnect')
            if player in q_oracle_queue:
                q_oracle_queue.remove(player)
                remove_from_queue(conn, player, 'disconnect')
            """3. Player is in questioner queue"""
            if player in questioner_queue:
                questioner_queue.remove(player)
                remove_from_queue(conn, player, 'disconnect')
            if player in q_questioner_queue:
                q_questioner_queue.remove(player)
                remove_from_queue(conn, player, 'disconnect')
            """4. Player did not start a game yet"""
            end_session(conn, player.session_id)

        print ('del: ' + str(sid))
        del players[sid]


def delete_game(players):
    """Remove dialogues"""
    for player in players:
        if player.dialogue_id is not None and player.dialogue_id in dialogues:
            del dialogues[player.dialogue_id]
        player.partner = None
        player.dialogue_id = None


@app.errorhandler(500)
def internal_error(error):
    print (error)
    return "500 error"

if async_mode == 'eventlet':
    eventlet.wsgi.server(eventlet.listen(('', int(os.environ['PORT']))), app)
