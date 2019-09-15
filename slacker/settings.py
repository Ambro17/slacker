import os

from dotenv import load_dotenv

load_dotenv()

# Flask env vars
ENV = os.getenv('FLASK_ENV', 'production')
DEBUG = ENV == 'development'
TESTING = False

# Alchemy env vars
SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Crypto secret
HASH_SECRET = os.environ['HASH_SECRET']
