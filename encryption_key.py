# Need to pip install cryptography
from cryptography.fernet import Fernet

FERNET_KEY = b'6aCI7dAGXJxrpVPXuhOoB4zS_szxcoNJr8q1_S4Hl6E=' # Insert the shared key
cipher = Fernet(FERNET_KEY)

hmac_key = b'cMm\x80j%.\xe3\x93\n\xb7Q\xf1T\x96\xff\x1e4|\xe6\x97R\xf5\xfb\xe6\x98\n\xa8\xbd$b\x8c'
