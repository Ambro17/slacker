class SlackerException(Exception):
    """Base exception for the bot."""

class RetroAppException(SlackerException):
    """Base exception for retroapp blueprint exceptions"""
