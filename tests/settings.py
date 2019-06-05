from dotenv import load_dotenv

load_dotenv('.env')
ENV = 'development'
TESTING = True
SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'
