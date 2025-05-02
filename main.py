import re

import Messenger

commPort = input("Comm channel? ")

Messenger = Messenger.Messenger(commPort)


print("{RYLR998} Finished setup")
while True:
    ui = input("MESSAGE: \n")
    Messenger.ChatMessage(ui)