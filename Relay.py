import random
import time
import threading
import Message
from Protocols import DirectMessage

MAX_HOPS = 5  # Prevent infinite flooding


class RelayManager:
    def __init__(self, messenger):
        self.futureRelayMessage = None  # Packet to get sent once a relay is found.
        self.DMC = None
        self.messenger = messenger
        self.responseThread = None
        self.expectedReplySEQ = None
        self.respondingToRelaySEQ = None
        self.success = False
        self.forwardRelayAcks = False
        self.forwardAddr = 0

    def relayCanReachClient(self, Message):
        print("[Relay] Client returned message")
        if Message.seqNum == self.DMC.pkt.seqNum:
            print("[Relay] Message collected!")
            if Message.ascii_to_binary(Message.flag)[7] == "1":
                print('[Relay] ACK Complete, this client can relay.')
                self.DMC.success = True
                self.Messenger.clearToSend = False
                self.Messenger.clearToSendIssueTime = time.time()
                self.DMResponse(Message)
                if self.DMC.responseThread == None:
                    return
                # self.DMC.responseThread.stop()



    def DMResponse(self, message):
        if self.responseThread == None:
            print("[Relay] Resposne window closed. Unable to act as relay.")
            return

        # self.responseThread.stop()
        # Send a response back saying
        print("[Relay] Successfully found the target, I'm able to relay!")
        RequestPacket = Message.Message()
        RequestPacket.flag = RequestPacket.binary_to_ascii("0000001100000100")  # Relay & ACK
        RequestPacket.toAddr = 0
        RequestPacket.seqNum = self.respondingToRelaySEQ
        self.expectedReplySEQ = RequestPacket.seqNum
        RequestPacket.messageTime = int(time.time())
        RequestPacket.msg = ""
        RequestPacket.data = RequestPacket.messageToCommand(RequestPacket)
        time.sleep(random.random() * 5)
        self.messenger.comm.send(RequestPacket.data, False)
        # This device will now act as a relay for a period of time.
        self.forwardRelayAcks = True


    def relayMessageIncoming(self, msgPkt):
        if msgPkt.ascii_to_binary(msgPkt.flag)[12] == "1":
            print("[Relay] I'm being asked to respond to a relay request.")
            if self.futureRelayMessage != None:
                print("[Relay] Asked to be relay, but already asking for a relay... ignoring")
                return
            # This means we reply if we can reach the given address
            # Get address from msg.
            msg = msgPkt.msg
            toAddr = msgPkt.asciiToInteger(msg)
            self.forwardAddr = toAddr
            self.respondingToRelaySEQ = msgPkt.seqNum

            time.sleep(random.random() * 10)

            DM = Message.Message()

            # Compose packet & override defaults.
            DM.flag = DM.binary_to_ascii("0000000000010100")  # Single CTS, Relay
            DM.seqNum = DM.binary_to_ascii("00" + format(random.getrandbits(14), '014b'))
            self.expectedReplySEQ = DM.seqNum
            DM.messageTime = int(time.time())
            DM.msg = ""
            DM.toAddr = toAddr
            DM.data = DM.messageToCommand(DM)

            self.messenger.comm.send(DM.data, False)
            print("[Relay] -> [DM] -> Waiting ack via DM")

            self.responseThread = threading.Thread(target=self.threadAwaitResponse, args=(30,))
            self.responseThread.start()
        elif msgPkt.ascii_to_binary(msgPkt.flag)[7] == "1":
            # If this is true, then we have a response to our request for relay.
            print("[Relay] found a node!")
            if msgPkt.seqNum == self.expectedReplySEQ:
                # if self.forwardRelayAcks:
                #     # Forward packet.
                #     print("[Relay] Forwarding packet")
                # else:
                self.DMResponse(msgPkt)

            if msgPkt.seqNum == self.respondingToRelaySEQ:
                # This would be the sender getting a response, OR the relay sending a relay.
                if self.forwardRelayAcks:
                    print("[Relay] Sender node is asking for a forwarded packet")
                    forward = msgPkt
                    forward.toAddr = self.forwardAddr
                    forward.flag = forward.ascii_to_binary("0000000000010000")
                    forward.data = forward.messageToCommand(forward)
                    self.messenger.comm.send(forward.data, False)
                    self.success = True
                else:
                    print("[Relay] Yipee! Node found!")
                    # Forward packet
                    forward = self.futureRelayMessage
                    forward.toAddr = msgPkt.fromAddr
                    forward.flag = forward.binary_to_ascii("0000000110000100")
                    forward.data = forward.messageToCommand(forward)
                    # Assume it arrives...
                    self.messenger.comm.send(forward.data, False)
                    self.success = True
                    self.responseThread.stop()
                    print("[Relay] Relay complete. Hoping message gets delivered.")


        elif msgPkt.ascii_to_binary(msgPkt.flag)[11] == "1": #Gets short circuited
            print("[Relay] I'm responding to a relay agent. Someone is trying to talk to me!")
            # We are going to reply to a potential relay actor. This means we are ack that we are going to send data through a relay.
            endClient = Message.Message()
            endClient.toAddr = 0  # BROADCAST.
            endClient.messageTime = int(time.time())
            endClient.flag = endClient.binary_to_ascii("0000000110000100")  # Double CTS and Relay
            endClient.seqNum = msgPkt.seqNum
            endClient.msg = ""  # Sending the TO ADDR as the first two chars.
            endClient.data = endClient.messageToCommand(endClient)
            self.messenger.comm.send(endClient.data, False)

        return

    def threadAwaitResponse(self, duration=90):
        time.sleep(duration)  # 90s CTS window is active.
        if not self.success:
            print("[RELAY] Failed to discover a relay, or receive a response.")
            self.futureRelayMessage = None  # Packet to get sent once a relay is found.
            self.DMC = None
            self.responseThread = None
            self.expectedReplySEQ = None
            self.respondingToRelaySEQ = None
            return

    # This is US, or this device requesting a relay.
    def askForRelay(self, msgPkt):
        # Step one is to form out packet
        requestingRelay = Message.Message()
        requestingRelay.toAddr = 0  # BROADCAST.
        requestingRelay.messageTime = int(time.time())
        requestingRelay.flag = requestingRelay.binary_to_ascii("0000000000011100")  #Double CTS and Relay
        requestingRelay.seqNum = requestingRelay.binary_to_ascii("00" + format(random.getrandbits(14), '014b'))
        requestingRelay.msg = msgPkt.integerToAscii(msgPkt.toAddr)  # Sending the TO ADDR as the first two chars.
        requestingRelay.data = requestingRelay.messageToCommand(requestingRelay)
        self.messenger.comm.send(requestingRelay.data, False)
        print(f"[RELAY] Searching for potential relays...")
        self.futureRelayMessage = msgPkt