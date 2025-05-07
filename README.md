# LoRa Chat
### Secure Peer-to-Peer and Broadcast Messaging over LoRa

## Overview
This project is a secure, LoRa-based messaging application that allows encrypted communication 
between multiple nodes using the RYLR998 LoRa modules. Messages can be sent in broadcast (group chat)
or direct (private chat) modes via a clean web-based UI.

## Features
- Symmetric AES encryption and HMAC-based message integrity
- Real-time messaging over LoRa with Flask + SocketIO backend
- Web-based chat UI with support for multiple rooms
- Address negotiation and training for device identification
- CTS/RTS mechanism and optional relay forwarding
- Threaded message listening and response timeout handling

## Project Structure

├── app.py               # Flask + SocketIO server, web routing & background listener\
├── index.html           # Frontend chat interface (select port, chat, UI logic)\
├── Comm.py              # Handles serial port I/O and LoRa AT command setup\
├── Message.py           # Handles message creation, parsing, encryption, HMAC\
├── DirectMessage.py     # Handles direct messages with retries and CTS logic\
├── Relay.py             # Broadcasts messages via relay and handles CTS ACKs\
├── HostsTracker.py      # Tracks known LoRa device addresses\
├── Training.py          # Device address negotiation & network initialization\
├── encryption_key.py    # Pre-shared Fernet key and HMAC key\
├── main.py              # Simple terminal-based test runner\
└── static/\
└── style.css        # (Optional) Web styling for the UI


## Setup Instructions
### Hardware Requirements
- LoRa RYLR998 modules 
- USB-to-Serial connection to host device
- Multiple nodes for testing P2P and broadcast
### Software Requirements
- Python 3.10+
- Pip packages: see requirements.txt

## Getting Started
### 1. Connect a LoRa Device 

Plug a RYLR998 LoRa module into a USB port. Ensure drivers for your OS are installed.

### 2. Start the Flask Server

python app.py

The app runs on http://localhost:5300 and provides a chat UI

### 3. Open the Web Interface

In the browser, select the appropriate serial port (e.g., COM3, /dev/ttyUSB0)

### 4. Sending Messages

- Select "Group Chat (Broadcast)" to message all devices
- Use "+ Compose new message" to choose a specific address from known devices.

## Security 

- Encryption: All messages are encrypted using AES (via Fernet) using a shared key.
- Authentication: Messages include an HMAC for integrity verification.
- Relay Support: If a message fails to reach the recipient directly, the system can broadcast a CTS and relay the message through another node.

## Protocol Design
index.html (UI) - Chat input, display, port selection\
app.py - Flask routes, SocketIO handlers, threading\
Comm.py - Serial communication (AT+commands)\
Message.py - Encryption, parsing, HMAC validation\
Relay.py - Hop-based routing with max-hop limit\
DirectMessage.py - CTS-based retires and fallback\
Training.py - Address negotiation, discovery

## Authors 
Developed @ NMSU - Spring 2025 Cellular Networks and Mobile Computing Programming Project.
- Jack Nolen
- Nathan Hoxworth
- Horacio Gonzalez
- Christian Garcia Rivero
