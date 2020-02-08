import os
from slack import WebClient
from dotenv import load_dotenv

load_dotenv()
Slack = WebClient(os.environ["BOT_TOKEN"])
slack_cli = Slack
OviBot = WebClient(os.environ["OVIBOT_TOKEN"])
PollsBot = WebClient(os.environ["POLLS_TOKEN"])
