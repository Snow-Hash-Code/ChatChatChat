from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import threading

app = Flask(__name__)
app.secret_key = "your_secret_key"
socketio = SocketIO(app)

# Configuración de MongoDB
client = MongoClient("mongodb+srv://nvrz:0823200108232001GGWP@nvrz.2wmvdie.mongodb.net/?retryWrites=true&w=majority")
db = client["chat_db"]
users_collection = db["users"]
messages_collection = db["messages"]

# Lista de mensajes del chat
chat_messages = []
chat_lock = threading.Lock()

# Función para manejar la lógica del chat en un hilo
def handle_chat():
    global chat_messages
    while True:
        with chat_lock:
            if chat_messages:
                message = chat_messages.pop(0)
                messages_collection.insert_one(message)
                print(f"Mensaje: {message}")
                socketio.emit("new_message", {"username": message["username"], "message": message["message"]})
        threading.Event().wait(1)

# Iniciar el hilo del chat
chat_thread = threading.Thread(target=handle_chat)
chat_thread.start()
