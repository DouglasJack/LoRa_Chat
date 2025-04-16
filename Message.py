import os


def ascii_to_binary(text: str) -> str:
    return ' '.join(format(ord(char), '08b') for char in text)


def binary_to_ascii(binary: str) -> str:
    return ''.join(chr(int(b, 2)) for b in binary.split())


def messageToCommand(messageClass):
    return f"AT+SEND={messageClass.toAddr},{messageClass.dataLength},{messageClass.flag}{binary_to_ascii("00011111")}{messageClass.msg}"

class Message:
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

    # Whenever you need to make a new message, as in a chat message.
    # You use this function
    def newMessage(self, messageData,messageAddress=0):
        # A message to be sent will always attach a CTS. Any message sent must wait a time for a response.
        self.flag = binary_to_ascii("00010000")
        self.toAddr = messageAddress
        if messageAddress == 0:
            self.broadCast = True

        self.msg = messageData
        self.dataLength = len(self.msg)+2  # +2 from the flag and spacer
        self.data = messageToCommand(self)

        print(self.data)
        return self

    # When a message is received, all the steps to decryption and flags are finished.
    def recievedMessage(self):
        return self
