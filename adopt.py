from flask import Flask, render_template, request, jsonify, redirect
from socket import gethostbyname, gethostname
from pymongo import MongoClient
from random import randint
from subprocess import run
from consul import Consul
from uuid import uuid4

app = Flask(__name__)

run(['docker-compose', f'-fmongo.yml', 'up', '-d'])

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

client = MongoClient('mongodb://localhost:27017/')
db = client['pets']
cats_collection = db['cats']

@app.route('/adopt')
def index():
    return render_template('adopt.html')

@app.route("/fetchrecords", methods=["POST", "GET"])
def fetchrecords():
    if request.method == 'POST':
        query = request.form['action']
        minimum_age = float(request.form['minimum_age'])
        maximum_age = float(request.form['maximum_age'])
        pet_color = request.form['pet_color']
        pet_sex = request.form['pet_sex']
        if query == '':
            productlist = list(cats_collection.find())
        else:
            query = [{"$match": {"age": {"$gte": minimum_age, "$lt": maximum_age}}}]
            if pet_color != 'all': query[0]['$match']['color'] = pet_color
            if pet_sex != 'all': query[0]['$match']['sex'] = pet_sex
            productlist = list(cats_collection.aggregate(query))
    return jsonify({'htmlresponse': render_template('response.html', productlist=productlist)})

@app.route("/", methods=["POST", "GET"])
def handle_index():
    return redirect(f"{get_service_address('gateway')}/", code=302)

@app.route("/login", methods=["POST", "GET"])
def handle_login():
    return redirect(f"{get_service_address('login')}/login", code=302)

@app.route("/articles", methods=["POST", "GET"])
def handle_articles():
    return redirect(f"{get_service_address('articles')}/articles", code=302)

service_id = register_service('adopt', 8003)
app.run(port=8003)

try:
    while True:
        pass
except KeyboardInterrupt:
    deregister_service(service_id)
    run(['docker-compose', f'-fmongo.yml', 'stop'])