"""Manage symmetric encryption of secrets"""
from cryptography.fernet import Fernet, InvalidToken


class Encrypter:
    def __init__(self, key=None):
        self.cypher = Fernet(key) if key else None

    def configure(self, key):
        self.cypher = Fernet(key)

    def encrypt(self, text: str) -> bytes:
        """Encrypt string into a bytes"""
        if not self.cypher:
            raise ValueError('Encrypter not configured')

        try:
            return self.cypher.encrypt(text.encode('UTF-8'))
        except UnicodeEncodeError:
            raise ValueError('Invalid string. Could not encode with utf-8 codec.')

    def decrypt(self, bytes_str: bytes) -> str:
        if not self.cypher:
            raise ValueError('Encrypter not configured')

        try:
            return self.cypher.decrypt(bytes_str).decode('UTF-8')
        except InvalidToken:
            raise ValueError('Kaker, you are not allowed to see this message')


Crypto = Encrypter()
