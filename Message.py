class Message:
    def __init__(self):
        self.flag = None  # This is the ascii character flag
        self.data = None  # Message data (or actual message itself)
        self.seqNum = None  # Random sequence number
        self.fromAddr = None  # Address from which the message was received (opt.)
        self.toAddr = None  # Address from which the message is to be sent (opt.)
        self.broadCast = False  # If enabled, message is broadcast.
        self.messageTime = None  # The time in which the message was created/sent/received.
        self.encryption = None  # Not sure on this yet.

    # Whenever you need to make a new message, as in a chat message.
    # You use this function
    def newMessage(self):
        return self

    # When a message is received, all the steps to decryption and flags are finished.
    def recievedMessage(self):
        return self
