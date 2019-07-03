import os
from dotenv import load_dotenv

load_dotenv()

# Flask env vars
ENV = os.getenv('FLASK_ENV', 'production')
DEBUG = ENV == 'development'

# Alchemy env vars
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'Missing DB EnvVar')
SQLALCHEMY_TRACK_MODIFICATIONS = False
