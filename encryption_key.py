# Need to pip install cryptography
from cryptography.fernet import Fernet

FERNET_KEY = b'KEY GOES HERE' # Insert the shared key
cipher = Fernet(FERNET_KEY)
