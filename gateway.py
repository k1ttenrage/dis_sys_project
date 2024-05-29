from flask import Flask, request, abort, render_template, redirect, session
from socket import gethostbyname, gethostname
from subprocess import run
from random import randint
from consul import Consul
from uuid import uuid4

CONSUL_HOST = "127.0.0.1"
CONSUL_PORT = 8500
CONSUL_CLIENT = Consul(host=CONSUL_HOST, port=CONSUL_PORT)

def register_service(service_name, service_port):
    service_id = str(uuid4())
    service_ip = gethostbyname(gethostname())
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

app = Flask(__name__)

run(['docker-compose', f'-fredis.yml', 'up', '-d'])

@app.route("/", methods=["POST", "GET"])
def handle_index():
    if request.method == "POST":
        return render_template('index.html'), 200
    elif request.method == "GET":
        return render_template('index.html'), 200
    else:
        abort(400)

@app.route("/login", methods=["POST", "GET"])
def handle_login():
    return redirect(f"{get_service_address('login')}/login", code=302)

@app.route("/articles", methods=["POST", "GET"])
def handle_articles():
    return redirect(f"{get_service_address('articles')}/articles", code=302)

@app.route("/adopt", methods=["POST", "GET"])
def handle_adopt():
    return redirect(f"{get_service_address('adopt')}/adopt", code=302)

service_id = register_service('gateway', 8000)
app.run(port=8000)

try:
    while True: 
        pass
except KeyboardInterrupt:
    deregister_service(service_id)
    run(['docker-compose', f'-fredis.yml', 'stop'])