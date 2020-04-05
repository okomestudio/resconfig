from enum import Enum


class Action(Enum):
    """Action performed by the update method."""

    ADDED = 1
    MODIFIED = 2
    REMOVED = 3
    RELOADED = 4
