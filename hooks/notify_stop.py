"""Stop: notify if main session, no active team, and agent idle.

3-layer filter:
  1. session_id in state (filters team members / unknown sessions)
  2. no active team in teams/ (filters intermediate Agent Teams stops)
  3. jsonl idle check (filters intermediate responses — agent still working)

Layer 3: spawn background monitor that checks if jsonl transcript is still growing.
If idle after IDLE_SECONDS → play sound (if elapsed > THRESHOLD_SECONDS).
"""
import sys
import json
import os
import time
import subprocess
import glob

STATE_PATH = os.path.join(os.path.expanduser("~"), ".claude", "hooks", ".notify_state.json")
TEAMS_DIR = os.path.join(os.path.expanduser("~"), ".claude", "teams")

# --- Customize these ---
WAV_PATH = "C:/Windows/Media/Windows Notify Calendar.wav"
THRESHOLD_SECONDS = 60
IDLE_SECONDS = 3

MONITOR_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notify_monitor.py")

try:
    payload = json.load(sys.stdin)
except Exception:
    sys.exit(0)

session_id = payload.get("session_id", "")
transcript_path = payload.get("transcript_path", "")

# Read state dict
if not os.path.exists(STATE_PATH):
    sys.exit(0)

try:
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        state = json.load(f)
except Exception:
    sys.exit(0)

# Purge stale entries (older than 2h)
now = time.time()
state = {k: v for k, v in state.items() if now - v < 7200}

# Filter 1: session_id must exist in state
if session_id not in state:
    sys.exit(0)

# Elapsed time (passed to monitor for sound threshold)
elapsed = time.time() - state[session_id]

# Filter 2: no active team owned by this session
if os.path.isdir(TEAMS_DIR):
    for config_path in glob.glob(os.path.join(TEAMS_DIR, "*/config.json")):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                team_config = json.load(f)
            if team_config.get("leadSessionId") == session_id:
                sys.exit(0)
        except Exception:
            continue

# Remove entry and write back
del state[session_id]
try:
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f)
except Exception:
    pass

# Filter 3: spawn background monitor to check jsonl idle, then notify
subprocess.Popen(
    [sys.executable, MONITOR_SCRIPT, transcript_path, str(IDLE_SECONDS), WAV_PATH,
     session_id, str(elapsed), str(THRESHOLD_SECONDS)],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
