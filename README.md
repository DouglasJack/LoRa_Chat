# Updates to Messenger.py

### Clear-to-Send (CTS) Timing Logic:
Added self.clearToSend and self.clearToSendIssueTime to prevent message spam collisons

Enforced a 5-second backoff between CTS acks and new outbound messages.

Tracked via self.lastMessageSent to support ACK/NACK retry mechanisms if needed in future implementations

# Updates to Message.py

### Packet Structure Standardization
- Added PACKET_SEPARATOR using 0x1F to separate structured fields in message body
- Updated messageToCommand() to generate LoRa-compatable AT+SEND strings with the packet format:
AT+SEND=|toAddr|dataLength|flag|fromAddr|seqNum|msg|timestamp|

### Message Encryption
- Added encryption support using the cryptography.fernet module:
  - Message content is encrypted in newMessage() before transmission.
  - Message content is decrypted in recievedMessage() if encryption is detected

### Timestamp Handling
- Automatically timestamps each new message
  - self.messageTime = int(time.time())

### Incoming Message Parsing
- Replaced .split(",") with .find() and .rfind() to handle encrypted payloads that may contain commas.
- Handles parsing of 
  - Addressing fields
  - DBM and SNR
  - Encrypted Payload
  - Sequence number and timestamp
    - last_comma = payload.rfind(",")

# test_encryption_packet.py
- Script used to test:
  - message encryption and packet construction
  - message decryption and parsing 
  - real or simulated communication with the LoRa module
- simulates end-to-end encryption, packetization, and parsing of a message

- for real LoRa device communication it utilizes the Messenger + Comm + Message stack
- Set USE_LORA_DEVICE = True for for real serial communication

# encryption_key.py
- Generated a one time key
- replace the FERNET_KEY = b'KEY GOES HERE' with provided key

