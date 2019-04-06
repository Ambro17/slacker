import os

from collections import defaultdict
from slackclient import SlackClient
from utils import make_answer

slack = SlackClient(os.getenv('BOT_TOKEN'))


def url_verification_handler(event):
    return event.get('challenge', 'Challenge not found')


def fallback_handler(event):
    return f"Unknown event {event}"


def event_dispatcher(event):
    slack.api_call(
        "chat.postMessage",
        channel="#general",
        text=f"Event {event.get('event')} received"
    )


event_type_handlers = defaultdict(
    lambda: fallback_handler,
    {
        'url_verification': url_verification_handler,
        'event_callback': event_dispatcher
    }
)


def dispatch_event(event):
    handler = event_type_handlers[event.get('type')]
    response = handler(event)
    if response:
        return make_answer(response)
