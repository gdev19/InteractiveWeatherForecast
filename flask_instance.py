from flask import Flask, send_from_directory

server = Flask(__name__)


@server.route("/static/<path:filename>")
def serve_static_files(filename):
    return send_from_directory(filename, static_url_path="static")
