import random
import re
import time
from encryption_key import cipher






PACKET_SEPARATOR = chr(0x1F)


def messageToCommand(messageClass):
    return f"AT+SEND={messageClass.toAddr},{messageClass.dataLength},{messageClass.flag}{chr(0x1F)}{messageClass.msg}{chr(0x1F)}{messageClass.seqNum}{chr(0x1F)}{messageClass.messageTime}"


class Message:
    def ascii_to_binary(self, text: str) -> str:
        return ' '.join(format(ord(char), '08b') for char in text)
    def binary_to_ascii(self, binary: str) -> str:
        # TODO, Ensure that anything sent here does not become the 0x1F character.
        return ''.join(chr(int(b, 2)) for b in binary.split())

    def __init__(self):
        self.flag = None  # This is the ascii character flag
        self.msg = None  # Message data (or actual message itself)
        self.seqNum = None  # Random sequence number
        self.fromAddr = None  # Address from which the message was received (opt.)
        self.toAddr = None  # Address from which the message is to be sent (opt.)
        self.broadCast = False  # If enabled, message is broadcast.
        self.messageTime = None  # The time in which the message was created/sent/received.
        self.encryption = None  # Not sure on this yet.

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
        self.flag = self.binary_to_ascii("00010000")
        self.toAddr = messageAddress
        self.fromAddr = 3  # CHANGE TO DEVICE ADDRESS

        self.seqNum = self.binary_to_ascii("0" + format(random.getrandbits(7),
                                                   '07b'))  # Generates a random sequence number where 0 is the beginning number.

        self.messageTime = int(time.time())
        self.msg = messageData
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

        self.dataLength = len(self.msg) + 5 + 10
        self.data = messageToCommand(self)

        print(f"[MessagePKT] {self.data}")
        return self

    def recievedMessage(self, message):
        # Split by our ascii US character.
        pattern = (  # ChatGPT generated Regex :)
                r"\+RCV=(\d+),"  # Address
                r"(\d+),"  # Length
                r"(.)" +  # Flag (any single ASCII character)
                re.escape(chr(0x1F)) +  # Splitter
                r"(.*?)" +  # Message (non-greedy)
                re.escape(chr(0x1F)) +  # Splitter
                r"(.)" +
                re.escape(chr(0x1F)) +  # Splitter
                r"(-?\d+)" +  # Time
                "," +  # SequenceNumber (any single ASCII character)
                r"(-?\d+)," +  # Signal Strength
                r"(-?\d+)"  # SNR
        )

        # This is kinda insecure. A vulnerability will be present here. because we don't strip symbols from the
        # message coming in.
        match = re.match(pattern, message)
        if match and len(match.groups()) == 8:
            chunks = match.groups()  # ('5', '6', '\x10', '<Cool message>', '!', '-13', '11')
            self.fromAddr = chunks[0]
            self.dataLength = chunks[1]
            self.flag = chunks[2]
            self.msg = chunks[3]
            self.seqNum = chunks[4]
            self.timeCode = chunks[5]
            self.DBM = chunks[6]
            self.SNR = chunks[7]

            if self.fromAddr == 0:
                self.broadCast = True

            try:
                decrypted = cipher.decrypt(self.msg.encode())
                self.msg = decrypted.decode()
                self.encryption = True

            except Exception as e:
                print(f"[Decryption] Failed to decrypt {e}")
                self.encryption = False

            print(f"[MessagePKT] RCV: {self.msg}")

            return self
        else:
            print("[MessagePKT] ERROR READING INCOMING MESSAGE - Could not split message chunks")
            print(message)

        return self
