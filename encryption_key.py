# Need to pip install cryptography
from cryptography.fernet import Fernet

FERNET_KEY = b'6aCI7dAGXJxrpVPXuhOoB4zS_szxcoNJr8q1_S4Hl6E=' # Insert the shared key
cipher = Fernet(FERNET_KEY)
