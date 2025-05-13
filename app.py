from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit
import Messenger as Messenger
import threading
import serial.tools.list_ports
import time

# Initialize Flask web application
app = Flask(__name__)
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")
app.secret_key = 'CellularNetworks'  # Secret key for session handling (storing selected COM port)

# Global variables
messenger = None  # Will hold the instance of Messenger class managing LoRa communication
received_messages = []  # List to store incoming messages for displaying on the web page

# ----------  helper to wrap UI events  ----------
def ui_emit(event, payload):
    """SocketIO emit that is safe even when called from a thread."""
    try:
        socketio.emit(event, payload)
    except RuntimeError:
        # called outside app context (background_listener)
        socketio.start_background_task(socketio.emit, event, payload)


# Background thread function to continuously check for received messages
# def background_listener():
#     global messenger
#     while True:
#         if messenger and messenger.messageCache:								    # Check if messenger is initialized and has cached messages
#             while messenger.messageCache:									        # Process all messages in the cache
#                 msg_obj = messenger.messageCache.pop(0)								# Remove and get the first message in the cache
#
#                 timestamp = time.strftime('%m-%d %H:%M', time.localtime(int(msg_obj.messageTime)))	# Convert epoch time to readable format
#                 new_message = f"[{timestamp}] {msg_obj.fromAddr}: {msg_obj.msg}"
#                 received_messages.append(new_message)								# Append message with timestamp
#                 socketio.emit('new_message', {'message': new_message})	# Send to UI
#
#         time.sleep(0.5)  # Add delay to avoid high CPU usage
def background_listener():
    global messenger
    while True:
        if messenger and messenger.messageCache:                                    # Check if messenger is initialized and has cached messages
            while messenger.messageCache:                                           # Process all messages in the cache
                pkt = messenger.messageCache.pop(0)                                 # Remove and get the first message in the cache

                ts = time.strftime('%m-%d %H:%M',
                                   time.localtime(int(pkt.messageTime)))
                line = f"[{ts}] {pkt.fromAddr}: {pkt.msg}"

                room_id = 0 if getattr(pkt, "broadCast", False) else int(pkt.fromAddr)
                ui_emit('new_message', {'room': room_id, 'message': line})
        time.sleep(0.5)


# Helper function to list all available serial ports on the system
def list_serial_ports():
    ports = serial.tools.list_ports.comports()  # Get list of port objects
    return [port.device for port in ports]  # Return only device names (e.g., COM3, /dev/ttyUSB0)

# Main route for displaying the chat UI and selecting serial port
@app.route('/', methods=['GET', 'POST'])
def index():
    global messenger
    ports = list_serial_ports()  # Get available ports to show in dropdown

    if request.method == 'POST':
        # Handle serial port selection form
        if 'comm_port' in request.form:
            selected_port = request.form.get('comm_port')                   # Get selected COM port from form
            session['comm_port'] = selected_port                            # Store it in session for later use
            messenger = Messenger.Messenger(selected_port, socketio=socketio)   # Initialize Messenger with selected port
        return redirect(url_for('index'))                                   # Refresh page after form submission

    comm_port = session.get('comm_port', None)  # Retrieve current port from session

    connected = comm_port if messenger else None

    # Render HTML page with current messages, selected port, and available ports
    return render_template('index.html', messages=received_messages, comm_port=connected, ports=ports)

# Listen for 'send_message' events from any connected client
# @socketio.on('send_message')
# def handle_send_message(data):
#     global messenger
#     message_text = data.get('message')                      # Extract the message content from the received data dictionary
#
#     if messenger and message_text:                          # Only proceed if a messenger is initialized and the message is not empty
#         messenger.ChatMessage(message_text)                 # Send the message out over the LoRa network
#
#         now = time.strftime('%m-%d %H:%M', time.localtime(int(time.time())))  # Create a timestamp for when the server handled the message
#
#         new_message = f"[{now}] You: {message_text}"        # Format the new message to include timestamp and sender ("You")
#
#         received_messages.append(new_message)               # Save the message to the server's local history
#
#         # Broadcast the new message to all connected web clients immediately
#         emit('new_message', {'message': new_message}, broadcast=True)
@socketio.on('send_message')
def handle_send_message(data):
    global messenger

    dest_addr = int(data.get('room', 0))     # 0 = broadcast
    msg_text  = data.get('message', '').strip()

    print(f"[Flask] →  dest={dest_addr}  {msg_text}")  # DEBUG LINE

    if messenger and msg_text:
        # LoRa side
        messenger.ChatMessage(msg_text, dest_addr)

        # echo back to every browser so they see their own line
        ts = time.strftime('%m-%d %H:%M', time.localtime())
        emit('new_message',
             {'room': dest_addr,
              'message': f"[{ts}] You: {msg_text}"},
             broadcast=True)

@socketio.on('get_hosts')
def send_known_hosts():
    if messenger:
        emit('host_list', messenger.hostTracker.knownHosts)
    else:
        emit('host_list', [])


# For sending Training status
@socketio.on('connect')
def handle_connect():
    if messenger and messenger.tr and messenger.tr.training_in_progress:
        emit('system_message',
             {'message': '🔄 Establishing connection… Training started (30 s)'})



if __name__ == '__main__':
    listener_thread = threading.Thread(target=background_listener, daemon=True)
    listener_thread.start()

    socketio.run(app, debug=True, port=5300, allow_unsafe_werkzeug=True)
