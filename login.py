from flask import Flask, request, abort, render_template, make_response, redirect, session
from base64 import b64encode
from subprocess import run
from uuid import uuid4
from time import sleep
from psycopg2.extras import register_uuid
from psycopg2.errors import DuplicateTable
from psycopg2 import connect, OperationalError
from hashlib import md5
from redis import Redis

register_uuid()

app = Flask(__name__)

app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'session:'
app.config['SESSION_REDIS'] = Redis(host='localhost', port=6379)

run(['docker-compose', f'-fpostgres.yml', 'up', '-d'])

def connect_to_db():
    while True:
        try:
            conn = connect("host=localhost dbname=user_db user=kittenrage password=123")
            cur = conn.cursor()
            return conn, cur
        except OperationalError:
            sleep(2)

def commit_close(conn, cur):
    conn.commit() 
    cur.close()
    conn.close()

def entry_by_user_id(user_id):
    conn, cur = connect_to_db()
    cur.execute('SELECT * FROM users WHERE user_id = %s;', (str(user_id),))
    entry = cur.fetchone()
    commit_close(conn, cur)
    return entry

try:
    conn, cur = connect_to_db()
    cur.execute("CREATE TABLE users (user_id uuid PRIMARY KEY, login varchar, password varchar, shelter int);")
    commit_close(conn, cur)
except DuplicateTable:
    cur.close()
    pass

@app.route("/login", methods=["POST", "GET"])
def handle_login():

    user_id = request.cookies.get('user_id')
    cookie = request.cookies.get('cookie')

    # automatic log in
    if user_id:
        entry = entry_by_user_id(user_id)
        if entry:
            if cookie == b64encode(str(entry[0]).encode() + entry[1].encode() + entry[2].encode()).decode(): 
                return redirect("http://127.0.0.1:8001/account", code=302)

    if request.method == "POST":
        login = request.form.get('login')
        password = md5(request.form.get('password').encode()).hexdigest()
        shelter = int(request.form.get('shelter')) #add dropdown list to html

        conn, cur = connect_to_db()
        cur.execute('SELECT * FROM users WHERE login = %s AND password = %s;', (login, password))
        entry = cur.fetchone()
        commit_close(conn, cur)

        if entry:
            # manual log in
            resp = make_response(render_template('account.html', value=login))
            user_id = str(entry[0])
            session[str(user_id)] = login
            cookie = b64encode(str(entry[0]).encode() + entry[1].encode() + entry[2].encode()).decode()
            resp.set_cookie('user_id', user_id)
            resp.set_cookie('cookie', cookie)
        
        else:
        # create account
            user_id = uuid4()
            session[str(user_id)] = login
            conn, cur = connect_to_db()
            cur.execute('INSERT INTO users (user_id, login, password, shelter) VALUES (%s, %s, %s, %s);', (user_id, login, password, shelter))
            commit_close(conn, cur)
            resp = make_response(render_template('account.html', value=login))
            user_id = str(user_id)
            cookie = b64encode(str(user_id).encode() + login.encode() + password.encode()).decode()
            resp.set_cookie('user_id', user_id)
            resp.set_cookie('cookie', cookie)

        return resp, 200
    
    elif request.method == "GET":
        return render_template('login.html'), 200
    
    else:
        abort(400)

@app.route("/account", methods=["POST", "GET"])
def handle_account():
    if request.method == "POST":
        resp = make_response(render_template('login.html'))
        session.pop(request.cookies.get('user_id'), None)
        print(session)
        resp.set_cookie('cookie', '', expires=0)
        resp.set_cookie('user_id', '', expires=0)
        return resp, 200
    elif request.method == "GET":
        user_id = request.cookies.get('user_id')
        login = entry_by_user_id(user_id)[1]
        resp = make_response(render_template('account.html', value=login))
        return resp, 200
    else:
        abort(400)

@app.route("/", methods=["POST", "GET"])
def handle_index():
    return redirect("http://127.0.0.1:8000/", code=302)

@app.route("/articles", methods=["POST", "GET"])
def handle_articles():
    return redirect("http://127.0.0.1:8002/articles", code=302)

@app.route("/adopt", methods=["POST", "GET"])
def handle_adopt():
    return redirect("http://127.0.0.1:8003/adopt", code=302)

@app.route("/help", methods=["POST", "GET"])
def handle_help():
    return redirect("http://127.0.0.1:8004/help", code=302)

app.run(port=8001)

try:
    while True:
        pass
except KeyboardInterrupt:
    cur.close()
    conn.close()
    run(['docker-compose', f'-fpostgres.yml', 'stop'])