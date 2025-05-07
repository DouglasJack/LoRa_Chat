import random
import threading
import time

import Message


class DirectMessage:
    def __init__(self, msg, dest=0):  # Must issue CTS
        self.Messenger = None
        self.responseThread = None
        self.msg = msg
        self.pkt = None
        self.dest = dest

        self.sendAttempts = 0
        self.success = False

        self.composePacket()

    def handleError(self, mCode, Messenger):
        print("[DM] Error occured, attempting resend.")
        self.send(Messenger)

    def threadAwaitResponse(self):
        time.sleep(30)
        if not self.success and self.sendAttempts <= 5:
            self.send(self.Messenger)

    def send(self, Messenger):
        self.Messenger = Messenger
        if self.sendAttempts > 1:
            print("[DM] Sending to address has failed, switching to [Relay]")
            packet_to_send = self.pkt.data
            self.Messenger.relay.broadcast_cts(self.dest, packet_to_send)
            return

        Messenger.clearToSend = True
        Messenger.clearToSendIssueTime = time.time() + 30
        Messenger.lastMessageSent = self  #Last message sent
        Messenger.comm.send(self.pkt.data)  # The message packet itself
        print("[DM] FLAG: " + self.pkt.flag)
        self.sendAttempts += 1

        self.Messenger = Messenger

        # Thread and wait response for 30s... If none by end time, abort.
        self.responseThread = threading.Thread(target=self.threadAwaitResponse)
        self.responseThread.start()

    def reply(self, Message):
        print("[DM] Received response from device.")
        if Message.seqNum == self.pkt.seqNum:
            print("[DM] Message collected!")
            # Same sequence number, this is a reply to this DMs message.
            # If not, ignore this message.
            if Message.ascii_to_binary(Message.flag)[8] == "1":
                print("[DM] Packet ack complete, ending.")
                # ACK and SeqNUM are toggled up. So we can
                self.success = True
                self.Messenger.clearToSend = False
                self.Messenger.clearToSendIssueTime = time.time()
                self.responseThread.stop()


    def composePacket(self):
        RequestPacket = Message.Message()
        RequestPacket.newMessage(self.msg)
        # RequestPacket = Message.Message()
        RequestPacket.flag = RequestPacket.binary_to_ascii("0000000000010000")
        RequestPacket.toAddr = self.dest
        # RequestPacket.seqNum = RequestPacket.binary_to_ascii("0" + format(random.getrandbits(7), '07b'))
        # RequestPacket.messageTime = int(time.time())
        # RequestPacket.msg = self.msg
        # RequestPacket.dataLength = len(RequestPacket.msg) + 5 + 10
        # RequestPacket.data = Message.messageToCommand(RequestPacket)
        self.pkt = RequestPacket