from flask import Flask, request, send_from_directory, render_template, redirect
from flask_socketio import SocketIO, emit, join_room # type: ignore
from threading import Thread
from typing import Any
from game import Game
from time import time, sleep
from json import dumps

app = Flask(__name__, static_folder="static")
app.config["SECRET_KEY"] = "pIvF83EHXOPh8S8iUSRRcBJMM4Vt98puOJIh_nsAQ2x05td82xPXO8TrCGe3X3OF9S6WxrtLQQQO7UkYX7fArcDHidg0UkeUF_BExbJi1beWD8L2wq5nFgVEVsSOgEBkjv5gStJpMGlcREK5R8nM4SPrSdlry1SwfgWRnvYxF6pRTxopfKHefDKcW_MBNjfOo37lDnlvP94roO4qhp_tsEUOQWntKT2BcNic0O_rm8okcna_0vxQj_8Qc6Bq1Ptt"
app.config["MAX_CONTENT_LENGTH"] = 1 << 10
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    max_http_buffer_size=0x100)

turn_duration = 0.3

game = Game()
board_str = dumps([
    {"row": obstacle.pos.row, "col": obstacle.pos.col, "tall": obstacle.tall}
    for obstacle in game.obstacles
])

last_update = time()
last_status: str = dumps(game.turn())

side: dict[str, bool] = {}

def run_game():
    global last_update, last_status
    while True:
        last_update = time()
        last_status = dumps(game.turn())
        socketio.emit("turn", last_status, to="left") # type: ignore
        socketio.emit("turn", last_status, to="right") # type: ignore
        sleep(turn_duration)

@socketio.on('connect')
def handle_connect():
    if request.remote_addr in side:
        join_room("right" if side[request.remote_addr] else "left")
        for i, player in enumerate(game.players):
            if player.team == side[request.remote_addr]:
                emit("move", {"p": i, "d": player.direction})

@socketio.on('move')
def handle_message(data: dict[str, Any]):
    try:
        assert request.remote_addr in side
        p = int(data["p"])
        assert game.players[p].team == side[request.remote_addr]
        d = int(data["d"])
        if d < 0 or d > 4:
            d = 4
        game.players[p].direction = d
        socketio.emit("move", {"p": p, "d": d}, to=("right" if side[request.remote_addr] else "left")) # type: ignore
    except:
        pass

@app.route("/left")
def left():
    if request.remote_addr and request.remote_addr not in side:
        side[request.remote_addr] = False
    return redirect("/")

@app.route("/right")
def right():
    if request.remote_addr and request.remote_addr not in side:
        side[request.remote_addr] = True
    return redirect("/")

@app.route("/")
def index():
    if request.remote_addr in side:
        return render_template("index.html",
            side=side[request.remote_addr],
            board=board_str,
            last_update=last_update,
            last_status=last_status,
            lscore=game.lscore,
            rscore=game.rscore,
            turn_duration=turn_duration
        )
    return render_template("select.html")

@app.route("/<path:filename>")
def return_static(filename: str = "index.html"):
    assert app.static_folder is not None
    return send_from_directory(app.static_folder, filename)

@app.errorhandler(404)
def debugging_required(_):
    return render_template("404.html"), 404

if __name__ == '__main__':
    t = Thread(target=run_game, daemon=True)
    t.start()
    app.run("0.0.0.0", 80, True)
