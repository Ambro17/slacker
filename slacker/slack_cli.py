import os
from slack import WebClient
from dotenv import load_dotenv

load_dotenv()
Cuervot = WebClient(os.environ["CUERVOT"])
OviBot = WebClient(os.environ["OVIBOT"])
Slack = slack_cli = Cuervot