import random
import threading
from os.path import exists

import Comm
import Message
import time

import Protocols.Training
from Protocols import DirectMessage, HostsTracker


def MessageToCodes(msg):
    match msg:
        case "+OK":
            return "OKAY!"
        case "+ERR=2":
            return "Head is not AT or String command"
        case "+ERR=4":
            return "Unkown command"
        case "+ERR=5":
            return "Data length does not match length of message"
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
    def __init__(self, sport, socketio=None):
        self.socketio = socketio
        self.myAddress = 0
        self.comm = Comm.Comm(sport, self)
        self.messageCache = []
        self.lastMessageSent = None
        self.clearToSend = False  # IF ENABLED, No messages can be sent
        self.clearToSendIssueTime = None
        self.hostTracker = HostsTracker.HostsTracker(self)
        time.sleep(1)  # This is required. (Used to setup thread in COMM)
        self.tr = Protocols.Training.Training(self)
        self.trainingThread = threading.Thread(target=self.tr.searching, daemon=True)
        self.trainingThread.start()

    def ackMessage(self, msg):
        print("[Messenger response]")
        print(msg.ascii_to_binary(msg.flag))
        if msg.ascii_to_binary(msg.flag)[11] == "1":
            time.sleep(random.random() * 5+.8)
            print("[Messenger] Acking message...")
            replyPacket = Message.Message()
            # replyPacket = replyPacket.newMessage("",msg.fromAddr)
            replyPacket.toAddr = msg.fromAddr
            replyPacket.msg = "ACK"
            replyPacket.seqNum = msg.seqNum
            replyPacket.flag = replyPacket.binary_to_ascii("0000000010000000")
            replyPacket.messageTime = int(time.time())
            replyPacket.data = replyPacket.messageToCommand(replyPacket)
            print("[Messenger] FLAG: " + replyPacket.flag)
            print("[Messenger] SEQ: " + replyPacket.seqNum)
            self.comm.send(replyPacket.data, False)


    def RecievedMessage(self, msg):
        # Converts message serial string into Messenger object.
        mCode = MessageToCodes(msg)
        if mCode:
            print("{RYLR998}: " + mCode + "\n")

            # Message packet. Call function on the message class which determines how to handle a message
            # Think of the message packet as containing all details about how to send and return.
            if mCode != "OKAY!" and self.lastMessageSent:
                self.lastMessageSent.handleError(mCode, self)
        else:
            # Should be a recieved message.
            MsgPacket = Message.Message()

            MsgPacket = MsgPacket.recievedMessage(msg)
            self.hostTracker.addHost(MsgPacket.fromAddr)

            if MsgPacket.ascii_to_binary(MsgPacket.flag)[10] == "1":
                # Address bit is raised, handle accordingly.
                self.tr.received(MsgPacket)
                return

            try:
                self.lastMessageSent.reply(MsgPacket)
            except AttributeError:
                print()

            self.ackMessage(MsgPacket)

            # For WebUI, only cache if it's from another device
            if MsgPacket.encryption:
                self.messageCache.append(MsgPacket)

    # When using CustomMessage, its expected you handle the packet creation yourself.
    def CustomMessage(self, Message, ignoreCTS=False):
        # Must pass Message class
        if ignoreCTS or not self.clearToSend:
            self.lastMessageSent = Message
            self.comm.send(Message.data, False)
            print("[Messenger] FLAG: " + Message.flag)
            print("[Messenger] SEQ: " + Message.seqNum)

    def ChatMessage(self, msg):
        if self.clearToSend and self.clearToSendIssueTime:
            if time.time() < self.clearToSendIssueTime:
                print("[Messenger]: CTS active. Message not sent.")
                return
        #MsgPacket = Message.Message()
        #MsgPacket.newMessage(msg)
        DM = DirectMessage.DirectMessage(msg)
        DM.send(self)

        # Creates a message packet, then sends it. The message will generate the correct data for sending the command.
        # self.clearToSend = True
        # self.clearToSendIssueTime = time.time() + 30
        # self.lastMessageSent = DM  #Last message sent
        # self.comm.send(DM.pkt) # The message packet itself
