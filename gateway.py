from flask import Flask, request, abort, render_template, redirect, session
from flask_session import Session
from subprocess import run

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

if __name__ == "__main__":
    app.run(port=8000)
    Session(app)

try:
    while True:
        pass
except KeyboardInterrupt:
    run(['docker-compose', f'-fredis.yml', 'stop'])