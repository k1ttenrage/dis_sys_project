from flask import Flask, request, abort, render_template, make_response, redirect, session
from socket import gethostbyname, gethostname
from requests import get, RequestException
from mariadb import connect, Error
from subprocess import run
from random import randint
from uuid import uuid4
from consul import Consul

app = Flask(__name__)

run(['docker-compose', f'-fmaria.yml', 'up', '-d'])

CONSUL_HOST = "127.0.0.1"
CONSUL_PORT = 8500
CONSUL_CLIENT = Consul(host=CONSUL_HOST, port=CONSUL_PORT)

def register_service(service_name, service_port):
    service_id = str(uuid4())
    service_ip = CONSUL_HOST
    CONSUL_CLIENT.agent.service.register(service_name,service_id=service_id, address=service_ip, port=service_port)
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

def get_connection():
    try:
        conn = connect(user="root", password="123", host="127.0.0.1", port=3306, database="articles")
    except Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
    return conn

@app.route("/", methods=["POST", "GET"])
def handle_index():
    return redirect(f"{get_service_address('gateway')}/", code=302)

@app.route("/login", methods=["POST", "GET"])
def handle_login():
    return redirect(f"{get_service_address('login')}/login", code=302)

@app.route("/articles", methods=["POST", "GET"])
def handle_articles():
    data = []
    cur = get_connection().cursor()
    cur.execute("SELECT * FROM articles_tbl")
    all = cur.fetchall()
    for article in all:
        data.append({'article_name':article[1],'article_text': article[2], 'article_author':article[3], 'article_date': article[4]})
    if request.method == "POST":
        resp = make_response(render_template('articles.html', articles=data))
        return resp, 200
    elif request.method == "GET":
        resp = make_response(render_template('articles.html', articles=data))
        return resp, 200
    else:
        abort(400)

@app.route("/adopt", methods=["POST", "GET"])
def handle_adopt():
    return redirect(f"{get_service_address('adopt')}/adopt", code=302)

@app.route("/create_article", methods=["POST", "GET"])
def handle_generator():
    try:
        response = get(f"{get_service_address('articles_generator')}/create_article")
        response.raise_for_status()
        return redirect(f"{get_service_address('articles_generator')}/create_article", code=302)
    except RequestException as e:
        print(f"Primary server not responding: {e}")

    return redirect(f"{get_service_address('articles_generator_backup')}/create_article", code=302)

service_id = register_service('articles', 8002)
app.run(port=8002)

try:
    while True:
        pass
except KeyboardInterrupt:
    deregister_service(service_id)
    run(['docker-compose', f'-fmaria.yml', 'stop'])