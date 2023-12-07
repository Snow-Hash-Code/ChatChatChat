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

# Vista principal para mostrar el chat
@app.route("/")
def index():
    if "username" in session:
        username = session["username"]
        
        # Recuperar mensajes de la base de datos
        messages = list(messages_collection.find({}, {"_id": 0}))

        return render_template("chat.html", username=username, messages=messages)
    
    return redirect(url_for("login"))


# Nueva ruta para obtener mensajes
@app.route("/get_messages")
def get_messages():
    messages = list(messages_collection.find({}, {"_id": 0}))
    return {"messages": messages}

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

# Vista para el registro de usuarios
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Verificar si el usuario ya existe
        if users_collection.find_one({"username": username}):
            return render_template("register.html", error="El usuario ya existe")

        # Hash de la contraseña antes de almacenarla
        hashed_password = generate_password_hash(password)

        # Almacenar el usuario en la base de datos
        users_collection.insert_one({"username": username, "password": hashed_password})

        return redirect(url_for("login"))

    return render_template("register.html")

# Vista para el inicio de sesión
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Buscar el usuario en la base de datos
        user = users_collection.find_one({"username": username})

        # Verificar si el usuario existe y la contraseña es correcta
        if user and check_password_hash(user["password"], password):
            session["username"] = username
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="Nombre de usuario o contraseña incorrectos")

    return render_template("login.html")

# Vista para cerrar sesión
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# Vista para enviar mensajes al chat
@app.route("/send_message", methods=["POST"])
def send_message():
    if "username" in session:
        username = session["username"]
        message_text = request.form["message"]
        message = {"username": username, "message": message_text}
        
        with chat_lock:
            chat_messages.append(message)

        return redirect(url_for("index"))

    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
