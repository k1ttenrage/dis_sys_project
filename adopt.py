from flask import Flask, render_template, request, jsonify, redirect, abort
from pymongo import MongoClient
from subprocess import run

app = Flask(__name__)

run(['docker-compose', f'-fmongo.yml', 'up', '-d'])

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
        minimum_price = float(request.form['minimum_price'])
        maximum_price = float(request.form['maximum_price'])
        if query == '':
            productlist = list(cats_collection.find().sort('pid', 1))
        else:
            productlist = list(cats_collection.find({'age': {'$gte': minimum_price, '$lte': maximum_price}}))
    return jsonify({'htmlresponse': render_template('response.html', productlist=productlist)})

@app.route("/", methods=["POST", "GET"])
def handle_index():
    return redirect("http://127.0.0.1:8000/", code=302)

@app.route("/login", methods=["POST", "GET"])
def handle_login():
    return redirect("http://127.0.0.1:8001/login", code=302)

@app.route("/articles", methods=["POST", "GET"])
def handle_articles():
    return redirect("http://127.0.0.1:8002/articles", code=302)

@app.route("/help", methods=["POST", "GET"])
def handle_help():
    return redirect("http://127.0.0.1:8004/help", code=302)

app.run(port=8003)

try:
    while True:
        pass
except KeyboardInterrupt:
    run(['docker-compose', f'-fmongo.yml', 'stop'])