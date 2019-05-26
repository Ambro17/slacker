from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///slackbot.db')
Session = sessionmaker(bind=engine)
S = Session()