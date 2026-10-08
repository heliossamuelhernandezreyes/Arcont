"""Process-safe advisory locks for cooperating Arcont project writers.

Lock files deliberately persist: unlinking a locked inode permits a second lock
domain. The operating system releases the lock if a writer crashes.
"""
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import time


@contextmanager
def document_lock(project: Path, relative: str, timeout: float = 15.0):
    root = Path(project).resolve()
    directory = root / ".arcont" / "locks"
    for part in (root / ".arcont", directory):
        if part.is_symlink():
            raise ValueError("symlink lock directory refused")
        part.mkdir(exist_ok=True)
    key = hashlib.sha256(relative.encode("utf-8")).hexdigest()
    path = directory / (key + ".lock")
    if path.is_symlink():
        raise ValueError("symlink lock file refused")
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    with os.fdopen(os.open(path, flags, 0o600), "r+b", buffering=0) as handle:
        if os.name == "nt":
            import msvcrt
            if os.fstat(handle.fileno()).st_size == 0:
                handle.write(b"\0")
            def acquire():
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            def release():
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            def acquire():
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            def release():
                fcntl.flock(handle, fcntl.LOCK_UN)
        deadline = time.monotonic() + timeout
        while True:
            try:
                acquire()
                break
            except (BlockingIOError, PermissionError):
                if time.monotonic() >= deadline:
                    raise ValueError("document is busy; retry after inspecting its revision")
                time.sleep(0.02)
        try:
            yield
        finally:
            release()
