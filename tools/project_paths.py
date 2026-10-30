"""Project-relative, bounded reads without following symlinks on POSIX."""
import os
from pathlib import Path, PurePosixPath
import stat


def project_path(root: Path, relative: str) -> Path:
    root = Path(root).resolve()
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise ValueError("safe project-relative path required")
    pure = PurePosixPath(relative)
    if pure.is_absolute() or ".." in pure.parts or pure.as_posix() != relative or pure.as_posix() == ".":
        raise ValueError("safe project-relative path required")
    current = root
    for part in pure.parts:
        current /= part
        if current.is_symlink():
            raise ValueError("symlink project path refused")
    if root not in current.resolve().parents:
        raise ValueError("project path escapes root")
    return current


def read_project_bytes(root: Path, relative: str, limit: int) -> bytes:
    path = project_path(root, relative)
    if os.name != "posix":
        if not path.is_file() or path.stat().st_size > limit:
            raise ValueError("project file is not regular or exceeds size limit")
        data = path.read_bytes()
    else:
        # Walk from a held root descriptor. O_NOFOLLOW on EVERY component
        # also rejects an ancestor swapped after the initial lexical check.
        descriptor = os.open(Path(root).resolve(), os.O_RDONLY | os.O_DIRECTORY)
        try:
            parts = PurePosixPath(relative).parts
            for part in parts[:-1]:
                next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
                os.close(descriptor)
                descriptor = next_fd
            fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptor)
            with os.fdopen(fd, "rb") as stream:
                info = os.fstat(stream.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
                    raise ValueError("project file is not regular or exceeds size limit")
                data = stream.read(limit + 1)
        finally:
            os.close(descriptor)
    if len(data) > limit:
        raise ValueError("project file exceeds size limit")
    return data
