from collections import defaultdict
from utils import make_response


def url_verification_handler(event):
    return event.get('challenge', 'Challenge not found')


def fallback_handler(event):
    return f"Unknown event {event}"


event_type_handlers = defaultdict(
    lambda: fallback_handler,
    {
        'url_verification': url_verification_handler
    }
)


def dispatch_event(event):
    handler = event_type_handlers[event.get('type')]
    response = handler(event)
    return make_response(response)
