from pathlib import Path
from typing import IO  # noqa
from typing import Callable  # noqa
from typing import Dict  # noqa
from typing import Generator  # noqa
from typing import Iterable  # noqa
from typing import List  # noqa
from typing import NewType  # noqa
from typing import Optional  # noqa
from typing import Set  # noqa
from typing import Text  # noqa
from typing import Tuple  # noqa
from typing import TypeVar  # noqa
from typing import Union

from .actions import Action

from typing import Any  # noqa; noqa


Key = Union[str, Tuple[str]]

WatchFunction = Callable[[Action, Any, Any], None]
"""Callback function, i.e., watcher, that triggers on an event happening at the key. It
takes in Action value, old, and new values.
"""

FilePath = Union[str, Path]

RT = TypeVar("RT")
