"""Stop: play sound if main session, elapsed time exceeds threshold, and no active team."""
import sys
import json
import os
import time
import subprocess
import glob

STATE_PATH = os.path.join(os.path.expanduser("~"), ".claude", "hooks", ".notify_state.json")
TEAMS_DIR = os.path.join(os.path.expanduser("~"), ".claude", "teams")
THRESHOLD_SECONDS = 60

# --- Customize your notification method here ---
WAV_PATH = "C:/Windows/Media/Windows Notify Calendar.wav"


def notify():
    """Play notification sound. Replace this with your preferred method."""
    try:
        subprocess.Popen(
            ["powershell", "-NoProfile", "-Command",
             f'(New-Object System.Media.SoundPlayer "{WAV_PATH}").PlaySync()'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


try:
    payload = json.load(sys.stdin)
except Exception:
    sys.exit(0)

session_id = payload.get("session_id", "")

# Read state dict
if not os.path.exists(STATE_PATH):
    sys.exit(0)

try:
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        state = json.load(f)
except Exception:
    sys.exit(0)

# Filter 1: session_id must exist in state (filters out team members and unknown sessions)
if session_id not in state:
    sys.exit(0)

# Filter 2: elapsed time must exceed threshold (filters short responses)
elapsed = time.time() - state[session_id]
if elapsed < THRESHOLD_SECONDS:
    sys.exit(0)

# Filter 3: no active team owned by this session (filters intermediate stops during Agent Teams)
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

# All filters passed — notify
notify()
