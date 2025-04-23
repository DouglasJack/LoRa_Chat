from os.path import exists

import Comm
import Message
import time

def MessageToCodes(msg):
    match msg:
        case "+OK":
            return "OKAY!"
        case "+ERR=2":
            return "Head is not AT or String command"
        case "+ERR=4":
            return "Unkown command"
        case "+ERR=10":
            return "TX is over times?"
        case "+ERR=12":
            return "CRC Error"
        case "+ERR=13":
            return "TX data exceeds 240Bytes"
        case "+ERR=14":
            return "Failed to write flash memory"
        case "+ERR=15":
            return "Unkown error"
        case "+ERR=17":
            return "Last TX was not completed"
        case "+ERR=18":
            return "Preamble value not allowed"
        case "+ERR=19":
            return "RX Failed, Header error"
        case "+ERR=20":
            return "Time setting value of smart receiving power is not allowed"
    return False


class Messenger:
    def __init__(self, sport):
        self.comm = Comm.Comm(sport, self)
        self.messageCache = []
        self.lastMessageSent = None
        self.clearToSend = False  # IF ENABLED, No messages can be sent
        self.clearToSendIssueTime = None  # This is the time of the last clearToSend issued, we cannot send if its been within 5s of CTS issued.

    def RecievedMessage(self, msg):
        # Converts message serial string into Messenger object.
        mCode = MessageToCodes(msg)
        if mCode:
            print("{RYLR998}: " + mCode + "\n")

            # Message packet. Call function on the message class which determines how to handle a message
            # Think of the message packet as containing all details about how to send and return.
            if mCode != "OKAY!" and self.lastMessageSent:
                self.lastMessageSent.handleError(mCode)
        else:
            # Should be a recieved message.
            MsgPacket = Message.Message()
            MsgPacket.recievedMessage(msg)

    def ChatMessage(self, msg):
        if self.clearToSend and self.clearToSendIssueTime:
            if time.time() - self.clearToSendIssueTime < 5:
                print("[Messenger]: CTS active. Message not sent.")
                return
        MsgPacket = Message.Message()
        MsgPacket.newMessage(msg)

        # Creates a message packet, then sends it. The message will generate the correct data for sending the command.
        self.lastMessageSent = MsgPacket #Last message sent
        self.comm.send(MsgPacket.data)
