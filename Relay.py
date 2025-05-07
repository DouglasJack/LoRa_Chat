import time
import threading
from Message import Message

MAX_HOPS = 5  # Prevent infinite flooding

class RelayManager:
    def __init__(self, messenger):
        self.messenger = messenger
        self.seen_messages = set()
        self.lock = threading.Lock()
        self.cts_ack_received = False
        self.responding_node = None
        self.awaited_cts_seq = None
        self.pending_message = None  # Stored message for CTS routing

    def has_seen(self, from_addr, seq_num):
        return (from_addr, seq_num) in self.seen_messages

    def mark_seen(self, from_addr, seq_num):
        with self.lock:
            self.seen_messages.add((from_addr, seq_num))

    def handle_incoming(self, raw, from_addr):
        pkt = Message()
        pkt = pkt.recievedMessage(raw)

        if not pkt or not pkt.flag or not pkt.seqNum:
            return

        seq_key = (pkt.fromAddr, pkt.seqNum)
        if self.has_seen(*seq_key):
            return
        self.mark_seen(*seq_key)

        # If the message is for me
        if pkt.toAddr == self.messenger.myAddress:
            print(f"[Relay] Received message for me: {pkt.msg}")
            return

        # Check if it's a CTS response
        if pkt.flag == '00100001' and pkt.seqNum == self.awaited_cts_seq:
            self.cts_ack_received = True
            self.responding_node = pkt.fromAddr
            return

        # Relay logic
        if len(pkt.hops) >= MAX_HOPS:
            print("[Relay] Max hops reached. Dropping message.")
            return

        pkt.hops.append(str(self.messenger.myAddress))
        relay_pkt = Message()
        relay_pkt.newMessage(pkt.msg, pkt.toAddr)
        relay_pkt.hops = pkt.hops
        self.messenger.comm.send(relay_pkt.data, False)
        print(f"[Relay] Forwarded message to {pkt.toAddr} via broadcast")

    def broadcast_cts(self, target, message, timeout=30):
        self.cts_ack_received = False
        self.responding_node = None
        self.awaited_cts_seq = str(int(time.time()))
        self.pending_message = message

        cts_pkt = Message()
        cts_pkt.newMessage("CTS", target)
        self.messenger.comm.send(cts_pkt.data, False)
        print(f"[CTS] Sent CTS for {target}, waiting {timeout}s for replies")

        threading.Thread(target=self.await_cts_response, args=(self.awaited_cts_seq, message)).start()

    def await_cts_response(self, seq, message):
        for _ in range(30):
            if self.cts_ack_received:
                print(f"[CTS] Got ACK from {self.responding_node} for SEQ {seq}")
                break
            time.sleep(1)

        if not self.cts_ack_received:
            print(f"[CTS] Timeout: No ACK received for SEQ {seq}")
            return

        msg_pkt = Message()
        msg_pkt.newMessage(message, self.responding_node)
        self.messenger.comm.send(msg_pkt.data, False)
        print(f"[Relay] Relayed message to {self.responding_node}")

        # Mark original DirectMessage as successful to stop retry loop
        if hasattr(self.messenger, "lastMessageSent") and self.messenger.lastMessageSent:
            self.messenger.lastMessageSent.success = True

    def send_with_cts(self, dest, msg):
        print(f"[Relay] Initiating relay to {dest}")
        self.broadcast_cts(dest, msg)
