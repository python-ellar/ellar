class UnsafeOperation(Exception):
    """The user did something suspicious"""


class UnsafeFileOperation(UnsafeOperation):
    """A Suspicious filesystem operation was attempted"""

    pass
