from pathlib import Path

from ..typing import FilePath


def ensure_path(path: FilePath) -> Path:
    return (path if isinstance(path, Path) else Path(path)).expanduser()
