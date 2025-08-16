import socket
import json
import pathlib
from pymongo import MongoClient
from datetime import datetime

SOCKET_HOST = "localhost"
SOCKET_PORT = 5000
MESSAGE_STORAGE = "storage/data.json"


def save_to_json(data: dict):
    """
    Додаткове збереження у JSON.
    """
    my_file = pathlib.Path(MESSAGE_STORAGE)
    storage = {}

    if my_file.is_file():
        with open(MESSAGE_STORAGE, "r", encoding="utf-8") as json_data:
            try:
                storage = json.load(json_data)
            except Exception as e:
                print(f"⚠️ Error reading JSON: {e}")

    storage.update({f"{datetime.now()}": data})

    with open(MESSAGE_STORAGE, "w", encoding="utf-8") as fh:
        json.dump(storage, fh, ensure_ascii=False, indent=4)


def run_socket_server():
    client = MongoClient("mongodb://localhost:27017/")
    db = client["messages_db"]
    collection = db["messages"]

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((SOCKET_HOST, SOCKET_PORT))
        server.listen(5)
        print(f"🔌 Socket server running on {SOCKET_HOST}:{SOCKET_PORT}")
        while True:
            conn, addr = server.accept()
            with conn:
                data = conn.recv(4096)
                if not data:
                    continue
                try:
                    msg = json.loads(data.decode("utf-8"))
                    # Зберігаємо у MongoDB
                    collection.insert_one(msg)
                    # Зберігаємо у JSON
                    save_to_json(msg)
                    print("✅ Message saved:", msg)
                except Exception as e:
                    print("❌ Error:", e)


if __name__ == "__main__":
    run_socket_server()
