from flask import Flask, request, send_from_directory, render_template, redirect
from flask_socketio import SocketIO, emit # type: ignore
from typing import Any

app = Flask(__name__, static_folder="static")
app.config["SECRET_KEY"] = "pIvF83EHXOPh8S8iUSRRcBJMM4Vt98puOJIh_nsAQ2x05td82xPXO8TrCGe3X3OF9S6WxrtLQQQO7UkYX7fArcDHidg0UkeUF_BExbJi1beWD8L2wq5nFgVEVsSOgEBkjv5gStJpMGlcREK5R8nM4SPrSdlry1SwfgWRnvYxF6pRTxopfKHefDKcW_MBNjfOo37lDnlvP94roO4qhp_tsEUOQWntKT2BcNic0O_rm8okcna_0vxQj_8Qc6Bq1Ptt"
app.config["MAX_CONTENT_LENGTH"] = 1 << 10
socketio = SocketIO(app, cors_allowed_origins="*")

side: dict[str, bool] = {}

# SocketIO 事件处理
@socketio.on('connect')
def handle_connect():
    print('客户端已连接')
    emit('server_response', {'data': '连接成功'})

@socketio.on('disconnect')
def handle_disconnect():
    print('客户端断开连接')

@socketio.on('client_message')
def handle_message(data: Any):
    print('收到消息:', data)
    # 广播给所有客户端
    emit('server_response', {'data': f'收到: {data}'}, broadcast=True)
    # 或回复给发送者
    emit('server_response', {'data': f'消息已处理; {request.remote_addr}'})

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
        return render_template("index.html", side=side[request.remote_addr])
    return render_template("select.html")

@app.route("/<path:filename>")
def return_static(filename: str = "index.html"):
    assert app.static_folder is not None
    return send_from_directory(app.static_folder, filename)

@app.errorhandler(404)
def debugging_required(_):
    return render_template("404.html"), 404

if __name__ == '__main__':
    app.run("0.0.0.0", 80, True)
