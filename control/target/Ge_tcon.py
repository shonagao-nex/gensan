import readline
import os
import datetime

HOME_DIR = os.path.expanduser("~")
HISTORY_FILE = os.path.join(HOME_DIR, ".Ge_tcon.history")
LOG_FILE = os.path.join(HOME_DIR, ".Ge_tcon.log")

# Load history if exists
if os.path.exists(HISTORY_FILE):
    try:
        readline.read_history_file(HISTORY_FILE)
    except Exception:
        pass

# Ensure history saved on exit
import atexit

def save_history():
    try:
        readline.write_history_file(HISTORY_FILE)
    except Exception:
        pass

atexit.register(save_history)


def log_command(command: str):
    try:
        timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a") as f:
            f.write(f"[{timestamp}] {command}\n")
    except Exception:
        pass


# --- existing code below (kept unchanged except where input is read) ---

# (The remainder of this file's existing logic should remain as-is.)

# NOTE: Insert 'log_command(command)' immediately after reading input
# from the user where command is the string read.
