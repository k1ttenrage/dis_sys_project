from flask import Flask, request, abort, render_template, make_response, redirect, session, url_for
from pika import BlockingConnection, ConnectionParameters
from mariadb import connect, Error
from uuid import uuid4
from redis import Redis
from json import loads

app = Flask(__name__)

app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'session:'
app.config['SESSION_REDIS'] = Redis(host='localhost', port=6379)

try:
    conn = connect(user="root", password="123",host="127.0.0.1", port=3306, database="articles")
    cur = conn.cursor()
except Error as e:
    print(f"Error connecting to MariaDB Platform: {e}")

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

article = {}

@app.route("/approve_article", methods=["POST", "GET"])
def handle_approve_article(article=article):
    global article_id, article_name, article_text, article_author, article_date
    login = session.get(request.cookies.get('user_id'), None)
    connection = BlockingConnection(ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='article_approve')
    method_frame, _, body = channel.basic_get(queue='article_approve', auto_ack=True)
    if method_frame: 
        article = loads(body.decode('utf-8')) 
        article_id = str(uuid4())
        article_name = article['article_name']
        article_text =  article['article_text']
        article_author = article['article_author']
        article_date = article['article_date']
        article['login'] = login

    if request.method == "POST":
        action = request.form['action']
        if action == 'approve':
            print(article_id, article_name, article_text, article_author, article_date, sep='\n')
            cur.execute("INSERT INTO articles_tbl (article_id,article_name,article_text,article_author, article_date) VALUES (?, ?, ?, ?, ?)", (article_id,article_name,article_text,article_author, article_date))
            conn.commit()
            cur.close()
        elif action == 'reject':
            article['login'] = login
            resp = make_response(render_template('article_approve.html', value=article))
            return resp, 200
        else:
            print('Unknown action')
        return redirect("http://127.0.0.1:8002/articles", code=302)
    
    elif request.method == "GET":
        article['login'] = login
        resp = make_response(render_template('article_approve.html', value=article))
        return resp, 200
    else:
        abort(400)


if __name__ == "__main__":
    app.run(port=8011)
