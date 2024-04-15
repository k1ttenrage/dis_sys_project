from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from subprocess import run

app = Flask(__name__)

run(['docker-compose', f'-fmongo.yml', 'up', '-d'])

client = MongoClient('mongodb://localhost:27017/')
db = client['pets']
cats_collection = db['cats']

cats = [
    {"name": "Whiskers", "age": 5, "breed": "Persian"},
    {"name": "Mittens", "age": 3, "breed": "Siamese"},
    {"name": "Felix", "age": 2, "breed": "Maine Coon"},
    {"name": "Luna", "age": 1, "breed": "Ragdoll"},
    {"name": "Simba", "age": 4, "breed": "Bengal"},
    {"name": "Tiger", "age": 6, "breed": "Siberian"},
    {"name": "Oreo", "age": 2, "breed": "British Shorthair"},
    {"name": "Shadow", "age": 3, "breed": "Scottish Fold"},
    {"name": "Smokey", "age": 4, "breed": "Norwegian Forest"},
    {"name": "Cleo", "age": 2, "breed": "Egyptian Mau"}
]

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

app.run(port=8000)

try:
    while True:
        pass
except KeyboardInterrupt:
    run(['docker-compose', f'-fmongo.yml', 'stop'])