from flask import Flask, request, abort, render_template, make_response, redirect, session
from pika import BlockingConnection, ConnectionParameters, BasicProperties
from subprocess import run
from datetime import date
from redis import Redis
from json import dumps

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
        resp = make_response(render_template('article_generator.html', value=login))
        return resp, 200
    elif request.method == "GET":
        resp = make_response(render_template('article_generator.html', value=login))
        return resp, 200
    else:
        abort(400)

if __name__ == "__main__":
    app.run(port=8012)

try:
    while True:
        pass
except KeyboardInterrupt:
    run(['docker-compose', f'-frabbitmq.yml', 'stop'])