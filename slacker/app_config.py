"""
Main module where env vars are imported and exported as constants.
"""
import os

from dotenv import load_dotenv

load_dotenv()

# Flask env vars
ENV = os.getenv('FLASK_ENV', 'production')
DEBUG = ENV == 'development'
TESTING = False

# Alchemy env vars
SQLALCHEMY_DATABASE_URI = DATABASE_URL = os.environ['DATABASE_URL']
SQLALCHEMY_TRACK_MODIFICATIONS = False
POSTGRES_USER = os.environ['POSTGRES_USER']

# Bot
CUERVOT = os.environ['BOT_TOKEN']
OVIBOT = os.environ['OVIBOT_TOKEN']
ROOMS_BOT = os.environ['ROOMS_BA_TOKEN']
CUERVOT_SIGNATURE = os.environ['CUERVOT_SIGNATURE']
OVIBOT_SIGNATURE = os.environ['OVIBOT_SIGNATURE']
ROOMS_BA_SIGNATURE = os.environ['ROOMS_BA_SIGNATURE']
POLLS_TOKEN = os.environ['POLLS_TOKEN']
POLLS_SIGNATURE = os.environ['POLLS_SIGNATURE']

BOT_FATHER = os.environ['BOT_FATHER']
ERRORS_CHANNEL = os.environ['ERRORS_CHANNEL']

# Crypto secret
HASH_SECRET = os.environ['HASH_SECRET']

# API secrets
CABA_CLI_ID = os.environ['CABA_CLI_ID']
CABA_SECRET = os.environ['CABA_SECRET']
HOYPIDO_USER = os.environ['HOYPIDO_USER']
HOYPIDO_TOKEN = os.environ['HOYPIDO_TOKEN']
HOYPIDO_MENU = os.environ['HOYPIDO_MENU']
CALENDAR_CLIENT = os.environ['CALENDAR_CLIENT']
CALENDAR_SECRET = os.environ['CALENDAR_SECRET']

# Task queue
CELERY_BROKER = os.environ['CELERY_BROKER']
CELERY_BACKEND = os.environ['CELERY_BACKEND']
