class SuspiciousOperation(Exception):
    """The user did something suspicious"""


class SuspiciousFileOperation(SuspiciousOperation):
    """A Suspicious filesystem operation was attempted"""

    pass
