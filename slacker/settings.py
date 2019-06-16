import os
from dotenv import load_dotenv

load_dotenv()

# Flask envvars
ENV = os.getenv('FLASK_ENV', 'production')
DEBUG = ENV == 'development'

# Alchemy envvars
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'Missing DB EnvVar')
SQLALCHEMY_TRACK_MODIFICATIONS = False
