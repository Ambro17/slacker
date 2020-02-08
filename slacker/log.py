import logging
import os

log_formatter = logging.Formatter(
    '%(asctime)s | %(levelname)s | %(module)s:%(filename)s:%(lineno)d | %(message)s'
)


def create_logger(name):
    # Set root logger to capture everything except told otherwise
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger = add_stdout_handler(logger)

    if _running_with_gunicorn():
        logger.info("Running with gunicorn. Extending handlers..")
        guni_logger = logging.getLogger('gunicorn.error')
        logger.handlers.extend(guni_logger.handlers)
        logger.info("Sucess")

    return logger


def add_stdout_handler(logger):
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(log_formatter)
    # Add the console handler to the logger object
    logger.addHandler(console_handler)
    return logger


def add_file_handler(logger):
    file_sink = logging.FileHandler('slacker.log')
    file_sink.setLevel(logging.DEBUG)
    file_sink.setFormatter(log_formatter)
    # Add the file handler to the logger object
    logger.addHandler(file_sink)
    return logger


def _running_with_gunicorn():
    return 'gunicorn' in os.getenv('SERVER_SOFTWARE', '')


logger = create_logger('slacker')
