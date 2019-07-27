import os
from slack import WebClient
from dotenv import load_dotenv

load_dotenv()
Slack = WebClient(os.environ["BOT_TOKEN"])
slack_cli = Slack
