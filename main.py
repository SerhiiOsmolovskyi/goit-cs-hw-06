import mimetypes
import pathlib
import json
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
from jinja2 import Environment, FileSystemLoader
from pymongo import MongoClient


SERVER_PORT = 3000
ASSETS_PATH = "./assets"

# Налаштування для socket-сервера
SOCKET_HOST = "localhost"
SOCKET_PORT = 5000


class HttpHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        data = self.rfile.read(int(self.headers["Content-Length"]))
        data_parse = urllib.parse.unquote_plus(data.decode())
        data_dict = {
            key: value for key, value in [el.split("=") for el in data_parse.split("&")]
        }

        # Відправка даних у socket-сервер
        self.save_messages(data_dict)

        # Редірект назад на головну
        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()

    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == "/":
            self.send_html_file("index.html")
        elif pr_url.path == "/message":
            self.send_html_file("message.html")
        elif pr_url.path == "/read":
            self.read_messages()
        else:
            if pathlib.Path().joinpath(ASSETS_PATH, pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file("error.html", 404)

    def send_html_file(self, filename, status=200, variables={}):
        env = Environment(loader=FileSystemLoader(ASSETS_PATH))
        template = env.get_template(f"{filename}")

        output = template.render(variables)

        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        self.wfile.write(output.encode())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", "text/plain")
        self.end_headers()
        with open(f"{ASSETS_PATH}{self.path}", "rb") as file:
            self.wfile.write(file.read())

    def save_messages(self, data: dict) -> None:
        """
        Замість JSON одразу — відправляємо дані на socket-сервер.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((SOCKET_HOST, SOCKET_PORT))
                sock.sendall(json.dumps(data).encode("utf-8"))
        except ConnectionRefusedError:
            print("❌ Socket-сервер не запущено! Дані не надіслані.")

    def read_messages(self) -> None:
        """
        Читаємо повідомлення з MongoDB.
        """
        client = MongoClient("mongodb://localhost:27017/")
        db = client["messages_db"]
        collection = db["messages"]

        messages = list(collection.find({}, {"_id": 0}))

        self.send_html_file("read.html", variables={"messages": messages})


def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ("", SERVER_PORT)
    http = server_class(server_address, handler_class)
    try:
        print(f"🌍 HTTP-сервер запущено на http://localhost:{SERVER_PORT}")
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()
        print("\n🛑 HTTP-сервер зупинено")


if __name__ == "__main__":
    run()
