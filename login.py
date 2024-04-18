from flask import Flask, request, abort, jsonify, render_template, make_response, redirect
from base64 import b64encode
from subprocess import run
from uuid import uuid4
from time import sleep
import psycopg2.extras
import requests
import psycopg2
import hashlib
psycopg2.extras.register_uuid()

run(['docker-compose', f'-fpostgres.yml', 'up', '-d'])

def connect_to_db():
    while True:
        try:
            conn = psycopg2.connect("host=localhost dbname=user_db user=kittenrage password=123")
            cur = conn.cursor()
            return conn, cur
        except psycopg2.OperationalError:
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
except psycopg2.errors.DuplicateTable:
    cur.close()
    pass

app = Flask(__name__)

@app.route("/login", methods=["POST", "GET"])
def handle_login():

    user_id = request.cookies.get('user_id')
    cookie = request.cookies.get('cookie')

    # automatic log in
    if user_id is not None:
        entry = entry_by_user_id(user_id)
        if entry is not None:
            if cookie == b64encode(str(entry[0]).encode() + entry[1].encode() + entry[2].encode()).decode(): 
                return redirect("http://127.0.0.1:8001/account", code=302)

    if request.method == "POST":
        login = request.form.get('login')
        password = hashlib.md5(request.form.get('password').encode()).hexdigest()
        shelter = int(request.form.get('shelter')) #add limit to html

        conn, cur = connect_to_db()
        cur.execute('SELECT * FROM users WHERE login = %s AND password = %s;', (login, password))
        entry = cur.fetchone()
        commit_close(conn, cur)

        if entry is None:
        # create account
            user_id = uuid4()
            conn, cur = connect_to_db()
            cur.execute('INSERT INTO users (user_id, login, password, shelter) VALUES (%s, %s, %s, %s);', (user_id, login, password, shelter))
            commit_close(conn, cur)
            resp = make_response(render_template('account.html', value=login))
            resp.set_cookie('user_id', str(user_id))
            resp.set_cookie('cookie', b64encode(str(user_id).encode() + login.encode() + password.encode()).decode())
        
        else:
            # manual log in
            resp = make_response(render_template('account.html', value=login))
            resp.set_cookie('user_id', str(entry[0]))
            resp.set_cookie('cookie', b64encode(str(entry[0]).encode() + entry[1].encode() + entry[2].encode()).decode())

        return resp, 200
    
    elif request.method == "GET":
        return render_template('login.html'), 200
    
    else:
        abort(400)

@app.route("/account", methods=["POST", "GET"])
def handle_account():
    if request.method == "POST":
        resp = make_response(render_template('login.html'))
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