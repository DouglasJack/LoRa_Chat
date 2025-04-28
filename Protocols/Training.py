# Training is used for the inital communication with RYLR998 Devices.
import math
import threading

import Message
import random
import time


def messageToCommand(messageClass):
    return f"AT+SEND={messageClass.toAddr},{messageClass.dataLength},{messageClass.flag}{chr(0x1F)}{messageClass.msg}{chr(0x1F)}{messageClass.seqNum}{chr(0x1F)}{messageClass.messageTime}"


def binary_to_ascii(binary: str) -> str:
    # TODO, Ensure that anything sent here does not become the 0x1F character.
    return ''.join(chr(int(b, 2)) for b in binary.split())


class Training:
    def __init__(self, messenger):
        self.messenger = messenger
        self.searchingSeqNum = 0
        # TODO: Move addressMessages to class for memorizing hosts.
        self.addressMessages = []  # This should NEVER be cleared during device operation.
        self.addressMessages.append(120)  # TODO: REMOVE
        self.addressMessages.append(1225)  # TODO: REMOVE

    def searching(self):
        print("LoRa Chat: Establishing an address. 30s...")
        # To begin, we will issue a message asking for others addresses.
        RequestPacket = Message.Message()
        RequestPacket.flag = RequestPacket.binary_to_ascii("00110000")
        RequestPacket.toAddr = 0
        RequestPacket.seqNum = RequestPacket.binary_to_ascii("0" + format(random.getrandbits(7), '07b'))
        RequestPacket.messageTime = int(time.time())
        RequestPacket.msg = "moawdawdawd"
        RequestPacket.dataLength = len(RequestPacket.msg) + 5 + 10
        RequestPacket.data = messageToCommand(RequestPacket)

        self.searchingSeqNum = RequestPacket.seqNum

        self.messenger.CustomMessage(RequestPacket, False)
        self.messenger.clearToSend = True
        self.messenger.clearToSendIssueTime = time.time() + 30  # CTS 30s window for replies on address initialization.
        time.sleep(30)  # We wait till CTS is open.
        # NOW, We assign our own address.


    def recieved(self,pkt):
        # Determine what the response is. If our CTS window is up, and our last packet contained the flag
        # Requesting the addresses and the sequence number is correct, then this is a response
        # Otherwise, this is a cry for help.
        # From this list of addresses we now have. Choose an address
        # from 1-10000 that is not in that range.
        nums = set(range(1, 10000)) - set(self.addressMessages)
        if nums:
            rand = random.choice(list(nums))
            self.messenger.comm.serial.write(str("AT+ADDRESS=" + str(rand) + "\r\n").encode())  # Direct comm writing.
            print("[Trainer] Chose & assigned address: " + str(rand))
        else:
            print("[Trainer] ALL ADDRESS HAVE BEEN CONSUMED!!!")

        # Clear CTS requirements.
        self.messenger.clearToSend = False
        self.messenger.clearToSendIssueTime = time.time()
        print("[Trainer] Completed training...")

    # Does the 16 bit conversions.
    def int_to_two_ascii(self, integer):

        # Convert integer to 16-bit binary string (zfill ensures leading zeros)
        binary_string = bin(integer)[2:].zfill(16)

        # Split the 16-bit binary string into two 8-bit chunks
        binary_chunk1 = binary_string[:8]
        binary_chunk2 = binary_string[8:]

        # Convert each 8-bit binary chunk to an integer
        int_chunk1 = int(binary_chunk1, 2)
        int_chunk2 = int(binary_chunk2, 2)

        # Convert each integer chunk to its corresponding ASCII character
        ascii_char1 = chr(int_chunk1)
        ascii_char2 = chr(int_chunk2)

        return ascii_char1, ascii_char2

    def threadedReply(self, pkt, offset):
        #TODO: Eventually this breaks down when generating address lists.
        #TODO: IF address lists are around 4, then it stops working?

        # Generates a host list
        addressesString = ""
        for id in self.addressMessages:
            char1, char2 = self.int_to_two_ascii(id)
            addressesString = f"{addressesString}{char1}{char2}"

        time.sleep(offset)
        RequestPacket = Message.Message()
        RequestPacket.flag = RequestPacket.binary_to_ascii("00100001")  # Just the init flag, NO CTS.
        RequestPacket.toAddr = pkt.fromAddr
        RequestPacket.seqNum = pkt.seqNum
        RequestPacket.messageTime = int(time.time())
        RequestPacket.msg = addressesString
        RequestPacket.dataLength = len(RequestPacket.msg) + 5 + 11
        RequestPacket.data = messageToCommand(RequestPacket)
        print("[Trainer] ADDRESSES: " + RequestPacket.msg)
        self.messenger.CustomMessage(RequestPacket, True)  # True can be used to force reply.

    def received(self, pkt):
        # Determine what the response is. If our CTS window is up, and our last packet contained the flag
        # Requesting the addresses and the sequence number is correct, then this is a response
        # Otherwise, this is a cry for help.
        if pkt.seqNum == self.searchingSeqNum:
            print("[Trainer] Addresses received from: " + pkt.fromAddr)
            #TODO: Set it up so it only adds addresses that aren't known.
            self.addressMessages.append(int(pkt.fromAddr))

            # GO through the message and strip out potential address lists.
            if len(pkt.msg) % 2 != 0 and len(pkt.msg) > 0:
                print("[Trainer] Error, addresses data is incorrect")
                return

            for i in range(0, len(pkt.msg), 2):
                char1 = pkt.msg[i]
                char2 = pkt.msg[i + 1]
                ascii_val1 = ord(char1)
                ascii_val2 = ord(char2)
                binary1 = bin(ascii_val1)[2:].zfill(8)
                binary2 = bin(ascii_val2)[2:].zfill(8)
                print("[Trainer] new address: " + str(binary1 + binary2))
                self.addressMessages.append(int(binary1 + binary2, 2))
                print(self.addressMessages)
        else:
            # Reply approved
            # Try to reply about your address.
            if pkt.ascii_to_binary(pkt.flag)[3] == "1":  # This is a reply message, because CTS is toggled up.
                #TODO: Check if our addres is in the initialization range, if so abort.
                print(self.messenger.myAddress)
                if self.messenger.myAddress > 65000:
                    print("[Trainer] You are in training mode. TODO: DO NOT REPLY IN TRAINING MODE.")

                offset = random.random() * 15  # offset of 15, gives us lots of padding and fits within 30s window.
                print("[Trainer] Replying to init of other device offset-> " + str(offset))
                pt = threading.Thread(target=self.threadedReply, args=(pkt, offset))
                pt.start()  # This is threaded because of the offset.
                # If 3 isn't toggled up, 3 = CTS

        return
