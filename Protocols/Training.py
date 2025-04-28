# Training is used for the inital communication with RYLR998 Devices.
import Message
import random
import time


def messageToCommand(messageClass):
    return f"AT+SEND={messageClass.toAddr},{messageClass.dataLength},{messageClass.flag}{chr(0x1F)}{messageClass.msg}{chr(0x1F)}{messageClass.seqNum}{chr(0x1F)}{messageClass.messageTime}"


class Training:
    def __init__(self, messenger):
        self.messenger = messenger

    def searching(self):
        print("LoRa Chat: Establishing an address. 30s...")
        # To begin, we will issue a message asking for others addresses.
        RequestPacket = Message.Message()
        RequestPacket.flag = RequestPacket.binary_to_ascii("00110000")
        RequestPacket.toAddr = 0
        RequestPacket.seqNum = RequestPacket.binary_to_ascii("0" + format(random.getrandbits(7), '07b'))
        RequestPacket.messageTime = int(time.time())
        RequestPacket.msg = ""
        RequestPacket.dataLength = len(RequestPacket.msg) + 5 + 10
        RequestPacket.data = messageToCommand(RequestPacket)

        self.messenger.CustomMessage(RequestPacket)
        self.messenger.clearToSend = True
        self.messenger.clearToSendIssueTime = time.time() + 30  # CTS 30s window for replies on address initialization.

    def recieved(self,pkt):
        # Determine what the response is. If our CTS window is up, and our last packet contained the flag
        # Requesting the addresses and the sequence number is correct, then this is a response
        # Otherwise, this is a cry for help.
        return
