from slack import WebClient
from slacker.app_config import CUERVOT, OVIBOT

Cuervot = WebClient(CUERVOT)
OviBot = WebClient(OVIBOT)
Slack = slack_cli = Cuervot