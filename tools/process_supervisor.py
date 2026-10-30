"""Own a command's process tree, including detached Linux descendants.

Each supervisor is a subreaper. Its parent death requests cancellation, so
terminating an outer bridge also cancels nested capability/adapter runners.
"""
from __future__ import annotations

import argparse
import ctypes
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


class Cancelled(Exception):
    pass


def _linux_guard():
    if not sys.platform.startswith("linux"):
        return
    parent = os.getppid()
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(36, 1, 0, 0, 0) or libc.prctl(1, signal.SIGTERM, 0, 0, 0):
        raise OSError(ctypes.get_errno(), "cannot establish process supervision")
    if os.getppid() != parent:
        raise Cancelled("parent exited during supervisor startup")


def _descendants():
    # /proc can be mounted from an ancestor PID namespace. Its numeric directory
    # names then differ from the PIDs accepted by os.kill in this namespace.
    own_status = Path("/proc/self/status").read_text()
    own_ids = next((line.split()[1:] for line in own_status.splitlines() if line.startswith("NSpid:")), [])
    if not own_ids or int(own_ids[-1]) != os.getpid():
        raise RuntimeError("cannot map supervisor PID namespace; cancellation is indeterminate")
    depth = len(own_ids) - 1
    own_kernel_pid = int(own_ids[0])
    parents = {}
    for path in Path("/proc").glob("[0-9]*/stat"):
        try:
            tail = path.read_text().rsplit(")", 1)[1].split()
            parents[int(path.parent.name)] = int(tail[1])
        except (OSError, ValueError, IndexError):
            continue
    found = set()
    while True:
        added = {pid for pid, parent in parents.items()
                 if parent == own_kernel_pid or parent in found} - found
        if not added:
            mapped = set()
            for pid in found:
                try:
                    status = Path(f"/proc/{pid}/status").read_text()
                    ids = next((line.split()[1:] for line in status.splitlines() if line.startswith("NSpid:")), [])
                except FileNotFoundError:
                    continue
                if len(ids) <= depth:
                    raise RuntimeError("cannot map descendant PID namespace")
                mapped.add(int(ids[depth]))
            return mapped
        found.update(added)


def _stop_tree(process):
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    else:
        # Snapshot before killing parents, then reap adopted detached children.
        children = _descendants() if sys.platform.startswith("linux") else set()
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        for pid in children:
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    process.wait(timeout=5)
    if sys.platform.startswith("linux"):
        deadline = time.monotonic() + 3
        while True:
            children = _descendants()
            for pid in children:
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            while True:
                try:
                    pid, _ = os.waitpid(-1, os.WNOHANG)
                except ChildProcessError:
                    pid = 0
                if pid == 0:
                    break
            if not _descendants():
                return
            if time.monotonic() >= deadline:
                raise RuntimeError("process termination remains indeterminate")
            time.sleep(.01)


def run(command, *, cwd=None, input=None, timeout=120, env=None, **options):
    """subprocess.run-compatible result, with supervised cancellation on timeout."""
    wrapper = [sys.executable, str(Path(__file__).resolve()), "--timeout", str(timeout), "--", *command]
    process = subprocess.Popen(wrapper, cwd=cwd, env=env, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        stdout, stderr = process.communicate(input, timeout=timeout + 10)
    except BaseException:
        process.terminate()
        try:
            process.communicate(timeout=8)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            error = subprocess.TimeoutExpired(command, timeout)
            error.process_tree_terminated = False
            raise error
        raise
    if process.returncode in (124, 125):
        error = subprocess.TimeoutExpired(command, timeout, output=stdout, stderr=stderr)
        error.process_tree_terminated = process.returncode == 124
        raise error
    if options.get("check") and process.returncode:
        raise subprocess.CalledProcessError(process.returncode, command, stdout, stderr)
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command or not 0 < args.timeout <= 21600:
        parser.error("command and timeout in (0,21600] required")
    def cancel(_signum, _frame):
        raise Cancelled("supervisor cancelled")
    signal.signal(signal.SIGTERM, cancel)
    signal.signal(signal.SIGINT, cancel)
    _linux_guard()
    deadline = time.time() + args.timeout
    inherited = os.environ.get("ARCONT_DEADLINE_EPOCH")
    if inherited is not None:
        limit = float(inherited)
        if not math.isfinite(limit):
            raise ValueError("invalid inherited process deadline")
        deadline = min(deadline, limit)
    if deadline <= time.time():
        print(json.dumps({"ok": False, "status": "timeout", "process_tree_terminated": True}))
        return 124
    data = sys.stdin.read()
    child_env = dict(os.environ, ARCONT_DEADLINE_EPOCH=str(deadline))
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, env=child_env, start_new_session=os.name == "posix")
    try:
        stdout, stderr = process.communicate(data, timeout=max(.001, deadline - time.time()))
        # A successful adapter must not leave a background writer behind either.
        _stop_tree(process)
    except (subprocess.TimeoutExpired, Cancelled):
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        try:
            _stop_tree(process)
            process.communicate(timeout=3)
            confirmed = sys.platform.startswith("linux")
            print(json.dumps({"ok": False, "status": "timeout" if confirmed else "indeterminate",
                              "process_tree_terminated": confirmed}))
            return 124 if confirmed else 125
        except Exception as exc:
            print(json.dumps({"ok": False, "status": "indeterminate", "error": str(exc)}))
            return 125
    sys.stdout.write(stdout)
    sys.stderr.write(stderr)
    return process.returncode if process.returncode >= 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
