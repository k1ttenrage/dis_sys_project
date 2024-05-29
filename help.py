from flask import Flask, request, abort, render_template, redirect

app = Flask(__name__)

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
    if request.method == "POST":
        return render_template('help.html'), 200
    elif request.method == "GET":
        return render_template('help.html'), 200
    else:
        abort(400)

if __name__ == "__main__":
    app.run(port=8004)