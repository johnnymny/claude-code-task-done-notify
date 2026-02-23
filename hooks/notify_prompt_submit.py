"""UserPromptSubmit: record session_id and timestamp for stop notification."""
import sys
import json
import os
import time

STATE_DIR = os.path.join(os.path.expanduser("~"), ".claude", "hooks")
STATE_PATH = os.path.join(STATE_DIR, ".notify_state.json")

try:
    payload = json.load(sys.stdin)
except Exception:
    sys.exit(0)

session_id = payload.get("session_id", "")
if not session_id:
    sys.exit(0)

# Read existing state dict
os.makedirs(STATE_DIR, exist_ok=True)
try:
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        state = json.load(f)
except Exception:
    state = {}

state[session_id] = time.time()

with open(STATE_PATH, "w", encoding="utf-8") as f:
    json.dump(state, f)
