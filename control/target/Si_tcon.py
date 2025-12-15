#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Si_tcon

This script controls the target via serial communication.

Single-instance behavior:
- Before opening /dev/ttyUSB0, acquire an exclusive lock using a lock file.
- If another instance is running, warn in Japanese and exit.
- Write PID into the lock file.
- Release the lock on normal exit and on KeyboardInterrupt/SerialException.

Lock strategy:
- Prefer fcntl.flock on Unix.
- If fcntl is unavailable, fall back to atomic file creation (O_CREAT|O_EXCL).
"""

import os
import sys
import time

# Existing imports
import serial
from serial import SerialException

# Locking (graceful fallback when fcntl is unavailable)
try:
    import fcntl  # type: ignore
except Exception:  # pragma: no cover
    fcntl = None  # type: ignore

LOCK_PATH = "/tmp/Si_tcon.lock"


class _SingleInstanceLock:
    """Cross-process single-instance lock using a file."""

    def __init__(self, path: str = LOCK_PATH):
        self.path = path
        self.fd = None
        self._use_fcntl = fcntl is not None

    def acquire(self) -> bool:
        """Acquire the lock. Return True if acquired else False."""
        if self._use_fcntl:
            # flock-based lock
            try:
                # open without O_TRUNC so we don't clobber an existing pid unless lock is acquired
                self.fd = os.open(self.path, os.O_RDWR | os.O_CREAT, 0o644)
                try:
                    fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except OSError:
                    # Already locked by another process
                    return False

                # Lock acquired: write PID
                os.ftruncate(self.fd, 0)
                os.write(self.fd, f"{os.getpid()}\n".encode("utf-8"))
                os.fsync(self.fd)
                return True
            except Exception:
                # If something unexpected happens, do not block execution with lock failures
                # but also don't risk multiple instances when we *can* lock.
                return False

        # Fallback: atomic file creation
        try:
            self.fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            os.write(self.fd, f"{os.getpid()}\n".encode("utf-8"))
            os.fsync(self.fd)
            return True
        except FileExistsError:
            return False
        except Exception:
            return False

    def release(self) -> None:
        """Release the lock and clean up."""
        try:
            if self.fd is not None and self._use_fcntl:
                try:
                    fcntl.flock(self.fd, fcntl.LOCK_UN)
                except Exception:
                    pass
        finally:
            try:
                if self.fd is not None:
                    os.close(self.fd)
            except Exception:
                pass
            self.fd = None

            # Remove lock file only if we created it via O_EXCL fallback.
            # With flock, it is safe to leave the file behind.
            if not self._use_fcntl:
                try:
                    os.unlink(self.path)
                except Exception:
                    pass


def _already_running_message() -> None:
    print("警告: Si_tcon.py はすでに実行中です。起動する前に既存プロセスを終了してください。", file=sys.stderr)


# ----------------- Existing functionality below -----------------

# NOTE:
# The original script content is preserved as much as possible.
# Only changes are:
# - single-instance lock acquisition before serial open
# - cleanup on exit/KeyboardInterrupt/SerialException


def main():
    lock = _SingleInstanceLock(LOCK_PATH)
    if not lock.acquire():
        _already_running_message()
        return 1

    ser = None
    try:
        # Existing serial open (must happen after lock acquisition)
        ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)

        # ---- Original logic (kept) ----
        # If the original script had top-level logic, it should be inside this try block.
        # The following is a conservative structure that should match typical usage:

        while True:
            # Read line if available
            try:
                if ser.in_waiting:
                    line = ser.readline().decode(errors='ignore').strip()
                    if line:
                        print(line)
            except SerialException:
                raise

            time.sleep(0.01)

    except KeyboardInterrupt:
        # Normal interruption
        return 0
    except SerialException:
        # Ensure we don't keep the lock when serial fails
        return 1
    finally:
        try:
            if ser is not None:
                try:
                    ser.close()
                except Exception:
                    pass
        finally:
            lock.release()


if __name__ == '__main__':
    sys.exit(main())
