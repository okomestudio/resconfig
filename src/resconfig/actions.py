from enum import Enum


class Action(Enum):
    """Action performed by the update method.

    The watch function receives this value as its first argument to change its behavior
    based on the action.
    """

    ADDED = 1
    """The item at the key has been added."""

    MODIFIED = 2
    """The item at the key has been modified."""

    REMOVED = 3
    """The item at the key has been removed."""

    RELOADED = 4
    """The item at the key has been reloaded."""
