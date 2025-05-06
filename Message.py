import random
import re
import time
from encryption_key import cipher
import hmac
import hashlib

SHARED_HMAC = b'cMm\x80j%.\xe3\x93\n\xb7Q\xf1T\x96\xff\x1e4|\xe6\x97R\xf5\xfb\xe6\x98\n\xa8\xbd$b\x8c'

PACKET_SEPARATOR = chr(0x1F)
DEFAULT_HOP_LIMIT = 3


class Message:
    def messageToCommand(self, messageClass):
        return f"AT+SEND={messageClass.toAddr},{len(f"{messageClass.flag}{chr(0x1F)}{messageClass.msg}{chr(0x1F)}{messageClass.seqNum}{chr(0x1F)}{messageClass.messageTime}")},{messageClass.flag}{chr(0x1F)}{messageClass.msg}{chr(0x1F)}{messageClass.seqNum}{chr(0x1F)}{messageClass.messageTime}"

    def ascii_to_binary(self, text: str) -> str:
        if len(text) != 2:
            raise ValueError("Only 2-character ASCII strings are supported.")
        for char in text:
            if not 0 <= ord(char) <= 127:
                raise ValueError("Characters must be 7-bit ASCII (0-127).")

        # Convert each character to 7-bit binary
        bin1 = format(ord(text[0]), '07b')
        bin2 = format(ord(text[1]), '07b')

        # Add '00' padding to make it 16 bits total
        return '00' + bin1 + bin2

    def binary_to_ascii(self, binary: str) -> str:
        binary = binary.replace(" ", "")
        if len(binary) != 16 or not all(bit in '01' for bit in binary):
            raise ValueError("Binary string must be exactly 16 bits and contain only '0' or '1'. "+str(len(binary)))

        if not binary.startswith("00"):
            raise ValueError("Binary string must start with '00' as prefix.")

        # Extract the two 7-bit chunks
        bin1 = binary[2:9]
        bin2 = binary[9:]

        char1 = chr(int(bin1, 2))
        char2 = chr(int(bin2, 2))

        return char1 + char2

    def __init__(self):
        self.flag = None  # This is the ascii character flag
        self.msg = None  # Message data (or actual message itself)
        self.seqNum = None  # Random sequence number
        self.fromAddr = None  # Address from which the message was received (opt.)
        self.toAddr = None  # Address from which the message is to be sent (opt.)
        self.broadCast = False  # If enabled, message is broadcast.
        self.messageTime = None  # The time in which the message was created/sent/received.
        self.encryption = None  # Not sure on this yet.
        self.hop_limit = DEFAULT_HOP_LIMIT # hop_limit attribute

        self.dataLength = 0  # This is used by Rylr to specify the size of the message
        self.data = None  # This is the full command string. This will get generated at newMessage or recievedMessage

        # Received message only
        self.SNR = 0
        self.DBM = 0
        self.received_from_addr = None # Track the immediate sender

    # Whenever you need to make a new message, as in a chat message.
    # You use this function
    def newMessage(self, messageData, messageAddress=0):
        messageData = re.sub(r'[^a-zA-Z0-9\s]', '', messageData)  # Replace symbols with nothing
        # A message to be sent will always attach a CTS. Any message sent must wait a time for a response.
        messageData = messageData.replace(PACKET_SEPARATOR, '')  # remove separator if present
        self.flag = self.binary_to_ascii("0000000000010000")
        self.toAddr = messageAddress
        self.fromAddr = 3  # CHANGE TO DEVICE ADDRESS

        self.seqNum = self.binary_to_ascii("00" + format(random.getrandbits(14), '014b'))  # Generates a random sequence number where 0 is the beginning number.

        self.messageTime = int(time.time())
        self.msg = messageData

        try:
            encrypted_data = cipher.encrypt(messageData.encode())
            self.msg = encrypted_data.decode()

            mac = hmac.new(SHARED_HMAC, self.msg.encode(), hashlib.sha256).hexdigest()
            self.msg = f"{self.msg}|HMAC:{mac}"
            self.encryption = True
        except Exception as e:
            print(f"[Encryption] Error encrypting message: {e}")
            self.msg = messageData
            self.encryption = False

        self.dataLength = len(self.msg) + 5 + 10
        self.data = self.messageToCommand(self)

        print(f"[MessagePKT] {self.data}")
        return self

    def handleError(self, mCode, messenger):
        return

    def recievedMessage(self, message):
        # Split by our ascii US character.
        # pattern = (
        #         r"\+RCV=,"  # Literal header (empty addr)
        #         r"(\d+),"  # Length
        #         r"(\d+),"  # Field
        #         r"(.{2})" + re.escape(chr(0x1f)) +  # Flag (2 any ASCII chars + SEP)
        #         r"(.*?)" + re.escape(chr(0x1f)) +  # Message (non-greedy to next SEP)
        #         r"(.{2})" + re.escape(chr(0x1f)) +  # Sequence (2 ASCII chars + SEP)
        #         r"(\d+),"  # ID (digits only)
        #         r"(-?\d+),"  # Signal strength
        #         r"(-?\d+)"  # SNR
        # )

        # This is kinda insecure. A vulnerability will be present here. because we don't strip symbols from the
        # message coming in.
        # match = re.match(pattern, message)
        # print(match)

        # REGEX SUCKS!

        if message.startswith("+RCV="):
            message = message[5:]  # Remove "+RCV="

        # Split by comma
        parts = message.split(',')

        # Base structure
        addr = parts[0]  # Could be empty
        length = parts[1]
        payload = parts[2]
        signal = parts[3]
        snr = parts[4]


        # Now split payload by SEP (0x1F)
        payload_parts = payload.split(chr(0x1f))

        # Extract details
        flag = payload_parts[0][:2]
        msg = payload_parts[1]
        seq = payload_parts[2][:2]
        timec = payload_parts[3]



        # Store in dictionary (table-like)
        result = {
            "address": addr,
            "length": int(length),
            "flag": flag,
            "message": msg,
            "sequence": seq,
            "time": int(timec),
            "signal": int(signal),
            "snr": int(snr)
        }

        # for k, v in result.items():
        #     print(f"{k}: {repr(v)}")

        if result and len(result) == 8:
            # chunks = match.groups()  # ('5', '6', '\x10', '<Cool message>', '!', '-13', '11')
            self.fromAddr = result["address"]
            self.dataLength = result["length"]
            self.flag = result["flag"]
            self.msg = result["message"]
            self.seqNum = result["sequence"]
            # self.timeCode = chunks["time"]
            #self.timeCode = chunks[5]
            self.messageTime = int(result["time"])  # Epoch seconds extracted from the packet

            self.DBM = result["signal"]
            self.SNR = result["snr"]

            if self.fromAddr == 0:
                self.broadCast = True

            try:
                decrypted = cipher.decrypt(self.msg.encode())
                decrypted_str = decrypted.decode()

                # Verify HMAC
                if "|HMAC:" in decrypted_str:
                    msg_parts = decrypted_str.rplit("|HMAC:", 1)
                    original_msg, received_msg = msg_parts[0], msg_parts[1]

                    expected_mac = hmac.new(SHARED_HMAC, original_msg.encode(), hashlib.sha256).hexdigest()

                    if not hmac.compare_digest(expected_mac, received_msg):
                        print("[AUTH] HMAC verification failed. Discarding Message")
                        return self
                    else:
                        self.msg = original_msg
                        print("[AUTH] HMAC verified.")
                        self.encryption = True
                else:
                    print("[AUTH] No HMAC found in message. Discarding Message")
                    return self
            except Exception as e:
                print("[Decryption] Error decrypting message: {e}")
                self.encryption = False

            print(f"[MessagePKT] RCV: {self.msg}")

            return self
        else:
            print("[MessagePKT] ERROR READING INCOMING MESSAGE - Could not split message chunks")
            print(message)

        return self
