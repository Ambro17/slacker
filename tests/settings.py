from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv('.env')
ENV = 'development'
TESTING = True

SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False

HASH_SECRET = Fernet.generate_key()
OVIBOT_TOKEN=1