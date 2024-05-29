from flask import Flask, request, abort, jsonify, render_template, make_response, redirect
from pika import BlockingConnection, ConnectionParameters, BasicProperties
from subprocess import run
from datetime import date
from time import sleep
import psycopg2
import json
import ast

app = Flask(__name__)

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

@app.route("/", methods=["POST", "GET"])
def handle_index():
    return redirect("http://127.0.0.1:8000/", code=302)

@app.route("/login", methods=["POST", "GET"])
def handle_login():
    return redirect("http://127.0.0.1:8001/login", code=302)

@app.route("/articles", methods=["POST", "GET"])
def handle_articles():
    return redirect("http://127.0.0.1:8002/articles", code=302)

@app.route("/adopt", methods=["POST", "GET"])
def handle_adopt():
    return redirect("http://127.0.0.1:8003/adopt", code=302)

@app.route("/help", methods=["POST", "GET"])
def handle_help():
    return redirect("http://127.0.0.1:8004/help", code=302)

@app.route("/approve_article", methods=["POST", "GET"])
def handle_approve_article():
    article = {}
    login = entry_by_user_id(request.cookies.get('user_id'))[1]
    article['login'] = login
    if request.method == "POST":
        action = request.form['action']
        if action == 'approve':
            print('Article Approved')
        elif action == 'reject':
            print( 'Article Rejected')
        else:
            print( 'Unknown action')
        resp = make_response(render_template('article_approve.html', value=article))
        return resp, 200
    elif request.method == "GET":
        connection = BlockingConnection(ConnectionParameters(host='localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='article_approve')
        method_frame, _, body = channel.basic_get(queue='article_approve', auto_ack=True)
        if method_frame: 
            article = json.loads(body.decode('utf-8')) 
        article['login'] = login
        resp = make_response(render_template('article_approve.html', value=article))
        return resp, 200
    else:
        abort(400)

if __name__ == "__main__":
    app.run(port=8011)
