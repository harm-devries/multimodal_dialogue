import random

# from threading import Thread

from flask import Flask, render_template
#from flask.ext.socketio import SocketIO
# from flask.ext.login import LoginManager, UserMixin, login_required

import socketio
# set this to 'threading', 'eventlet', or 'gevent'
async_mode = 'eventlet'

if async_mode == 'eventlet':
    import eventlet
    eventlet.monkey_patch()
elif async_mode == 'gevent':
    from gevent import monkey
    monkey.patch_all()

sio = socketio.Server(logger=True, async_mode=async_mode)
app = Flask(__name__)
app.wsgi_app = socketio.Middleware(sio, app.wsgi_app)
app.config['SECRET_KEY'] = 'secret!'
thread = None
# sio = SocketIO(app)
# login_manager = LoginManager()
# login_manager.init_app(app)

clients_name = {}
clients_waiting = {}
clients_partner = {}


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/game')
def game():
    return render_template('game.html')

@sio.on('add user', namespace='/game')
def add_username(sid, username):
    clients_name[sid] = username
    sio.emit('usercount', {'num_users': len(clients_name)}, namespace='/game')


@sio.on('newquestion', namespace='/game')
def new_question(sid, message):
    print 'neq question'
    print message
    sio.emit('newquestion', message,
             room=clients_partner[sid], namespace='/game')


@sio.on('new answer', namespace='/game')
def new_answer(sid, message):
    sio.emit('new answer', message,
             room=clients_partner[sid], namespace='/game')


@sio.on('next', namespace='/game')
def next(sid):
    print "next"
    partnerid = False
    for id, user in clients_waiting.items():
        if id != sid and user:
            partnerid = id

    if partnerid:
        clients_partner[partnerid] = sid
        clients_partner[sid] = partnerid
        role = (random.random() > 0.5)
        imageid = random.randint(1, 10)
        if role:
            sio.emit('questioner',
                     {'data': '<img class="img-responsive img-rounded" src="static/{}.jpg" />'.format(imageid)},
                     room=id,
                     namespace='/game')
            sio.emit('answerer',
                     {'data': '<img class="img-responsive img-rounded" src="static/{}.jpg" />'.format(imageid)},
                     room=sid,
                     namespace='/game')
        else:
            sio.emit('answerer',
                     {'data': '<img class="img-responsive img-rounded" src="static/{}.jpg" />'.format(imageid)},
                     room=id,
                     namespace='/game')
            sio.emit('questioner',
                     {'data': '<img class="img-responsive img-rounded" src="static/{}.jpg" />'.format(imageid)},
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
    print 'connect'

# @sio.on('disconnect', namespace='/game')
# def disconnect(sid):
#     print clients_name
#     del clients_name[sid]
#     sio.emit('usercount',
#              {'num_users': len(clients_name)},
#              namespace='/game')


if __name__ == '__main__':
    if async_mode == 'threading':
        # deploy with Werkzeug
        app.run(threaded=True)
    elif async_mode == 'eventlet':
        # deploy with eventlet
        import eventlet
        eventlet.wsgi.server(eventlet.listen(('', 5000)), app)
    elif async_mode == 'gevent':
        # deploy with gevent
        from gevent import pywsgi
        try:
            from geventwebsocket.handler import WebSocketHandler
            websocket = True
        except ImportError:
            websocket = False
        if websocket:
            pywsgi.WSGIServer(('', 5000), app,
                              handler_class=WebSocketHandler).serve_forever()
        else:
            pywsgi.WSGIServer(('', 5000), app).serve_forever()
    else:
        print('Unknown async_mode: ' + async_mode)
