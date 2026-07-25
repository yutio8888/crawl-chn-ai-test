#!/usr/bin/env python3
"""Run a command with a portable timeout and optional PTY transcript.

The exit contract matches GNU timeout for the cases used by the ZH tooling:
the child status is preserved, and an expired deadline returns 124 after the
entire child process group has been terminated.
"""

from __future__ import annotations

import argparse
import errno
import fcntl
import os
import pty
import selectors
import signal
import struct
import subprocess
import sys
import termios
import time
from pathlib import Path


TIMEOUT_EXIT = 124
TERMINATE_GRACE_SECONDS = 1.0


def _shell_status(returncode: int) -> int:
    return 128 + -returncode if returncode < 0 else returncode


def _signal_group(process: subprocess.Popen[bytes], signum: int) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signum)
    except ProcessLookupError:
        pass


def _terminate_group(process: subprocess.Popen[bytes]) -> None:
    _signal_group(process, signal.SIGTERM)
    try:
        process.wait(timeout=TERMINATE_GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        _signal_group(process, signal.SIGKILL)
        process.wait()


def _deadline(timeout: float) -> float:
    return time.monotonic() + timeout


def _remaining(deadline: float) -> float:
    return max(0.0, deadline - time.monotonic())


def _run_plain(command: list[str], timeout: float) -> int:
    process = subprocess.Popen(command, start_new_session=True)
    interrupted = 0

    def forward(signum: int, _frame: object) -> None:
        nonlocal interrupted
        interrupted = signum
        _signal_group(process, signum)

    previous = {
        signum: signal.signal(signum, forward)
        for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)
    }
    try:
        deadline = _deadline(timeout)
        while process.poll() is None:
            if interrupted:
                _terminate_group(process)
                return 128 + interrupted
            remaining = _remaining(deadline)
            if remaining == 0:
                _terminate_group(process)
                return TIMEOUT_EXIT
            try:
                process.wait(timeout=min(0.1, remaining))
            except subprocess.TimeoutExpired:
                pass
        return _shell_status(process.returncode)
    finally:
        for signum, handler in previous.items():
            signal.signal(signum, handler)
        if process.poll() is None:
            _terminate_group(process)


def _set_pty_size(fd: int) -> None:
    # Match the deterministic terminal geometry used by the UI bot.
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))


def _run_pty(command: list[str], timeout: float, transcript_path: Path) -> int:
    transcript_path.parent.mkdir(parents=True, exist_ok=True)
    master_fd, slave_fd = pty.openpty()
    _set_pty_size(slave_fd)
    process: subprocess.Popen[bytes] | None = None
    interrupted = 0

    def forward(signum: int, _frame: object) -> None:
        nonlocal interrupted
        interrupted = signum
        if process is not None:
            _signal_group(process, signum)

    previous = {
        signum: signal.signal(signum, forward)
        for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)
    }
    selector = selectors.DefaultSelector()
    try:
        process = subprocess.Popen(
            command,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            start_new_session=True,
        )
        os.close(slave_fd)
        slave_fd = -1
        os.set_blocking(master_fd, False)
        selector.register(master_fd, selectors.EVENT_READ)
        deadline = _deadline(timeout)
        timed_out = False

        with transcript_path.open("wb") as transcript:
            while selector.get_map():
                if process.poll() is None:
                    if interrupted:
                        _terminate_group(process)
                    elif _remaining(deadline) == 0:
                        timed_out = True
                        _terminate_group(process)
                wait_for = min(0.1, _remaining(deadline))
                if process.poll() is not None:
                    wait_for = 0.1
                for key, _events in selector.select(wait_for):
                    try:
                        chunk = os.read(key.fd, 65536)
                    except OSError as exc:
                        if exc.errno == errno.EIO:
                            chunk = b""
                        else:
                            raise
                    if chunk:
                        transcript.write(chunk)
                        transcript.flush()
                    else:
                        selector.unregister(key.fd)
            if process.poll() is None:
                if interrupted:
                    _terminate_group(process)
                elif _remaining(deadline) == 0:
                    timed_out = True
                    _terminate_group(process)
                else:
                    process.wait(timeout=_remaining(deadline))
            returncode = process.returncode
        if interrupted:
            return 128 + interrupted
        return TIMEOUT_EXIT if timed_out else _shell_status(returncode)
    except subprocess.TimeoutExpired:
        if process is not None:
            _terminate_group(process)
        return TIMEOUT_EXIT
    finally:
        selector.close()
        for signum, handler in previous.items():
            signal.signal(signum, handler)
        if process is not None and process.poll() is None:
            _terminate_group(process)
        if slave_fd >= 0:
            os.close(slave_fd)
        os.close(master_fd)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, required=True)
    parser.add_argument("--pty-transcript", type=Path)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be greater than zero")
    if args.command[:1] == ["--"]:
        args.command = args.command[1:]
    if not args.command:
        parser.error("a command is required after --")
    return args


def main() -> int:
    args = _parse_args()
    try:
        if args.pty_transcript is not None:
            return _run_pty(args.command, args.timeout, args.pty_transcript)
        return _run_plain(args.command, args.timeout)
    except FileNotFoundError as exc:
        print(f"command not found: {exc.filename}", file=sys.stderr)
        return 127


if __name__ == "__main__":
    raise SystemExit(main())
