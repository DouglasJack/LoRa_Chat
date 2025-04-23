import os
import random
import re
import base64
import time
from encryption_key import cipher

# Packet separator for consistent structure
PACKET_SEPARATOR = chr(0x1F)

def ascii_to_binary(text: str) -> str:
    return ' '.join(format(ord(char), '08b') for char in text)


def binary_to_ascii(binary: str) -> str:
    # TODO, Ensure that anything sent here does not become the 0x1F character.
    return ''.join(chr(int(b, 2)) for b in binary.split())


def messageToCommand(messageClass):
    packet_fields = [
        messageClass.toAddr,
        messageClass.dataLength,
        messageClass.flag + PACKET_SEPARATOR +
        str(messageClass.fromAddr) + PACKET_SEPARATOR +
        messageClass.seqNum + PACKET_SEPARATOR +
        messageClass.msg + PACKET_SEPARATOR +
        str(messageClass.messageTime)
    ]
    return f"AT+SEND={','.join(map(str, packet_fields))}"


class Message:
    def __init__(self):
        self.flag = None  # This is the ascii character flag
        self.msg = None  # Message data (or actual message itself)
        self.seqNum = None  # Random sequence number
        self.fromAddr = None  # Address from which the message was received (opt.)
        self.toAddr = None  # Address from which the message is to be sent (opt.)
        self.broadCast = False  # If enabled, message is broadcast.
        self.messageTime = None  # The time in which the message was created/sent/received.
        self.encryption = None

        self.dataLength = 0  # This is used by Rylr to specify the size of the message
        self.data = None  # This is the full command string. This will get generated at newMessage or recievedMessage

        # Received message only
        self.SNR = 0
        self.DBM = 0

    # Whenever you need to make a new message, as in a chat message.
    # You use this function
    def newMessage(self, messageData, messageAddress=0):
        messageData = re.sub(r'[^a-zA-Z0-9\s]', '', messageData)  # Replace symbols with nothing
        # A message to be sent will always attach a CTS. Any message sent must wait a time for a response.
        messageData = messageData.replace(PACKET_SEPARATOR, '')  # remove separator if present
        self.flag = binary_to_ascii("00010000")
        self.toAddr = messageAddress
        self.fromAddr = 3 # CHANGE TO DEVICE ADDRESS

        self.seqNum = binary_to_ascii("0" + format(random.getrandbits(7), '07b'))  # Generates a random sequence number where 0 is the beginning number.

        self.messageTime = int(time.time())
        self.msg = messageData
        self.dataLength = len(self.msg) + 4
        self.data = messageToCommand(self)

        # Encrypt the message
        try:
            encrypted_data = cipher.encrypt(messageData.encode())
            self.msg = encrypted_data.decode()
            self.encryption = True
        except Exception as e:
            print(f"[Encryption] Error encrypting message: {e}")
            self.msg = messageData
            self.encryption = False

        self.dataLength = len(self.msg) + 4
        self.data = messageToCommand(self)

        print(f"[MessagePKT] {self.data}")
        return self


    # When a message is received, all the steps to decryption and flags are finished.
    def recievedMessage(self, message):
        try:
            if "=" not in message:
                return self

            # RYLR998 header
            header, payload = message.split("=", 1)
            if not header.startswith("+RCV"):
                return self

            # Split into body + signal values
            last_comma = payload.rfind(",")
            second_last_comma = payload.rfind(",", 0, last_comma)
            if last_comma == -1 or second_last_comma == -1:
                raise ValueError("Could not locate DBM and SNR")

            self.DBM = payload[second_last_comma + 1:last_comma]
            self.SNR = payload[last_comma + 1:]

            main_part = payload[:second_last_comma]

            # Find and split (safe from commas in encrypted msg)
            first_comma = main_part.find(",")
            second_comma = main_part.find(",", first_comma + 1)
            third_comma = main_part.find(",", second_comma + 1)

            self.toAddr = main_part[:first_comma]
            self.dataLength = main_part[first_comma + 1:second_comma]
            self.flag = main_part[second_comma + 1]  # First character only

            packet_payload = main_part[third_comma + 1:]  # After 3rd comma, start of encoded message

            payload_fields = packet_payload.split(PACKET_SEPARATOR)
            if len(payload_fields) < 5:
                raise ValueError("Missing payload fields")

            self.fromAddr = payload_fields[1]
            self.seqNum = payload_fields[2]
            self.msg = payload_fields[3]
            self.messageTime = int(payload_fields[4])
            if self.fromAddr == '0':
                self.broadCast = True

            # Decrypt message
            try:
                decrypted = cipher.decrypt(self.msg.encode())
                self.msg = decrypted.decode()
                self.encryption = True
                print(f"[Decryption] Decrypted message: {self.msg}")
            except Exception as e:
                print(f"[Decryption] Error decrypting message: {e}")
                self.encryption = False

            print(f"[MessagePKT] RCV: {self.msg}")
            return self

        except Exception as e:
            print(f"[MessagePKT] ERROR: Could not parse message - {e}")
            return self
