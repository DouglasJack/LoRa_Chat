import math
import random

import serial
import threading

import Messenger


# Must pip install pyserial
# This class handles anything SERIAL. Messages to be returned, or sent.
# All messages recieved are sent to Messages


class Comm:
    def __init__(self, port, messenger):
        self.networkid = 3  # Network ID MUST be the same for all devices. We use 3
        self.serialPort = port
        self.stopThread = False

        self.messenger = messenger

        try:
            self.serial = serial.Serial(self.serialPort, 115200)
            # self.serial.write(str("AT+MODE=2,3000,9000\r\n").encode())  # CLASS C
            self.serial.write(str("AT+NETWORKID=" + str(self.networkid) + "\r\n").encode())

            newAddr = (math.ceil(random.random() * 383)) + 16000
            self.messenger.myAddress = newAddr
            self.serial.write(str("AT+ADDRESS=" + str(newAddr) + "\r\n").encode())
            print("[COMM] Default assigned ADDR: "+str(newAddr))

            self.thread = threading.Thread(target=self._listener, daemon=True)  # Daemon allows background threading.
            self.thread.start()

        except serial.SerialException as e:
            print(f"Error{e}")

    def __str__(self):
        return f"Comm port open on {self.serialPort}"

    def _listener(self):
        while not self.stopThread:
            try:
                response = self.serial.readline().decode().strip()
                if response:
                    self.messenger.RecievedMessage(response)
            except Exception as E:
                print(f"Exception {E}")

    # All messages MUST be sent as a broadcast.
    def send(self, message, skipDecode=False):
        print("[COMM] SENDING: " + str(message + "\r\n"))
        message = message + "\r\n"
        if skipDecode:
            message = message.encode("ascii", "ignore").decode("ascii")
        else:
            message = message.encode("ascii")

        # print(message)
        self.serial.write(message)
        # self.serial.write((message + "\r\n").encode("ascii"))
