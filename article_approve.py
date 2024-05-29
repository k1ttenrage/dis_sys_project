from flask import Flask, request, abort, render_template, make_response, redirect, session, url_for
from pika import BlockingConnection, ConnectionParameters
from mariadb import connect, Error
from uuid import uuid4
from redis import Redis
from json import loads

from consul import Consul
from os import getenv
from uuid import uuid4
from random import randint
CONSUL_HOST = "127.0.0.1"
CONSUL_PORT = 8500
CONSUL_CLIENT = Consul(host=CONSUL_HOST, port=CONSUL_PORT)

def register_service(service_name, service_port):
    service_id = str(uuid4())
    service_ip = getenv('SERVICE_IP', 'localhost')
    CONSUL_CLIENT.agent.service.register(
        service_name,
        service_id=service_id,
        address=service_ip,
        port=service_port
    )
    return service_id

def deregister_service(id):
    return CONSUL_CLIENT.agent.service.deregister(id)

def get_service_address(service_name):
    _, services = CONSUL_CLIENT.catalog.service(service_name)
    service = randint(0, len(services) - 1)
    if services:
        address = services[service]['ServiceAddress']
        port = services[service]['ServicePort']
        return f"http://{address}:{port}"
    else:
        raise Exception(f"Service '{service_name}' not found in Consul.")

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
    return redirect(f"{get_service_address('gateway')}/", code=302)

@app.route("/login", methods=["POST", "GET"])
def handle_login():
    return redirect(f"{get_service_address('login')}/login", code=302)

@app.route("/articles", methods=["POST", "GET"])
def handle_articles():
    return redirect(f"{get_service_address('articles')}/articles", code=302)

@app.route("/adopt", methods=["POST", "GET"])
def handle_adopt():
    return redirect(f"{get_service_address('adopt')}/adopt", code=302)

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
        return redirect(f"{get_service_address('articles')}/articles", code=302)
    
    elif request.method == "GET":
        article['login'] = login
        resp = make_response(render_template('article_approve.html', value=article))
        return resp, 200
    else:
        abort(400)



service_id = register_service('articles_approve', 8011)
app.run(port=8011)

try:
    while True: 
        pass
except KeyboardInterrupt:
    deregister_service(service_id)
    exit()

deregister_service(service_id)
exit()