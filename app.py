from flask import Flask, render_template, request, redirect, url_for, session
import Messenger as Messenger
import threading
import serial.tools.list_ports
import time

# Initialize Flask web application
app = Flask(__name__)
app.secret_key = 'CellularNetworks'  # Secret key for session handling (storing selected COM port)

# Global variables
messenger = None  # Will hold the instance of Messenger class managing LoRa communication
received_messages = []  # List to store incoming messages for displaying on the web page

# Background thread function to continuously check for received messages
def background_listener():
    global messenger
    while True:
        if messenger and messenger.messageCache:  # Check if messenger is initialized and has cached messages
            while messenger.messageCache:  # Process all messages in the cache
                msg_obj = messenger.messageCache.pop(0)  # Remove and get the first message in the cache
                received_messages.append(f"{msg_obj.fromAddr}: {msg_obj.msg}")  # Append formatted message to display list
        time.sleep(0.5)  # Add delay to avoid high CPU usage

# Helper function to list all available serial ports on the system
def list_serial_ports():
    ports = serial.tools.list_ports.comports()  # Get list of port objects
    return [port.device for port in ports]  # Return only device names (e.g., COM3, /dev/ttyUSB0)

# Main route handling both GET and POST requests
@app.route('/', methods=['GET', 'POST'])
def index():
    global messenger
    ports = list_serial_ports()  # Get available ports to show in dropdown

    if request.method == 'POST':
        # Handle serial port selection form
        if 'comm_port' in request.form:
            selected_port = request.form.get('comm_port')   # Get selected COM port from form
            session['comm_port'] = selected_port            # Store it in session for later use
            messenger = Messenger.Messenger(selected_port)  # Initialize Messenger with selected port
        # Handle message sending form
        elif 'message' in request.form:
            message_text = request.form.get('message')      # Get message text from form
            if messenger and message_text:
                messenger.ChatMessage(message_text)         # Send message using Messenger instance
                received_messages.append(f"You: {message_text}")  # Show sent message
        return redirect(url_for('index'))                       # Refresh page after form submission

    comm_port = session.get('comm_port', None)  # Retrieve current port from session
    # Render HTML page with current messages, selected port, and available ports
    return render_template('index.html', messages=received_messages, comm_port=comm_port, ports=ports)

if __name__ == '__main__':
    listener_thread = threading.Thread(target=background_listener, daemon=True)
    listener_thread.start()

    app.run(debug=True, port=5000)
