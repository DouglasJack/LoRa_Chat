import time
from Message import Message
from encryption_key import cipher

# Set this True to actually send via serial
USE_LORA_DEVICE = False

def simulate_send_receive():
    print("\nSimulating LoRa Encryption + Decryption Packet Test\n")

    # Simulate sending a message
    sender_addr = 4
    recipient_addr = 2

    message_text = "Hello! This is a secure test message."
    print(f"[SENDER] Sending to {recipient_addr}: {message_text}\n")

    msg = Message()
    msg.fromAddr = sender_addr
    msg.newMessage(message_text, messageAddress=recipient_addr)

    # Show generated AT+SEND command
    print("[DEBUG] AT Command (encrypted):")
    print(msg.data)

    # Simulate receiving the same message
    fake_rcv_msg = f"+RCV={recipient_addr},{msg.dataLength},{msg.flag}{chr(0x1F)}{msg.fromAddr}{chr(0x1F)}{msg.seqNum}{chr(0x1F)}{msg.msg}{chr(0x1F)}{msg.messageTime},-13,10"

    print("\n[SIMULATING RECEIVE] Incoming Message:")
    print(fake_rcv_msg)

    # Run decryption
    incoming = Message()
    incoming.recievedMessage(fake_rcv_msg)

    print(f"\n[DECRYPTED RESULT]: {incoming.msg}\n")

def send_to_lora_device():
    from Comm import Comm
    from Messenger import Messenger

    print("\nSending test message via real LoRa device...\n")
    comm_port = input("Enter your COM port (e.g., COM4): ").strip()
    M = Messenger(comm_port)

    test_message = "Live test from encryption test script!"
    M.ChatMessage(test_message)

    print("Message sent. Watch your serial console or the receiving device.")

if __name__ == "__main__":
    if USE_LORA_DEVICE:
        send_to_lora_device()
    else:
        simulate_send_receive()
