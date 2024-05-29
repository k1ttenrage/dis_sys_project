from flask import Flask, request, abort, render_template, make_response, redirect, session, flash
from pika import BlockingConnection, ConnectionParameters, BasicProperties
from subprocess import run
from datetime import date
from redis import Redis
from json import dumps

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

run(['docker-compose', f'-frabbitmq.yml', 'up', '-d'])

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

@app.route("/create_article", methods=["POST", "GET"])
def handle_create_article():
    article = {}
    login = session.get(request.cookies.get('user_id'), 'Не знайдено!')
    if login == 'Не знайдено!': login = None
    if request.method == "POST":
        article['article_name'] = request.form['article_name']
        article['article_text'] = request.form['article_text']
        article['article_author'] = login
        article['article_date'] =  str(date.today())
        connection = BlockingConnection(ConnectionParameters(host='localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='article_approve')
        channel.basic_publish(exchange='', routing_key='article_approve', body=dumps(article), properties=BasicProperties(delivery_mode = 2, ))
        flash('Стаття відправлена на огляд')
        resp = make_response(render_template('article_generator.html', value=login))
        return redirect(f"{get_service_address('articles')}/articles", code=302)
    elif request.method == "GET":
        resp = make_response(render_template('article_generator.html', value=login))
        return resp, 200
    else:
        abort(400)

service_id = register_service('articles_generator', 8010)
app.run(port=8010)

try:
    while True: 
        pass
except KeyboardInterrupt:
    deregister_service(service_id)
    exit()