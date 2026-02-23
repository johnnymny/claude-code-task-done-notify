# claude-code-task-done-notify

Sound notification when Claude Code finishes a long-running task.

[日本語](README.md)

## What is this?

When Claude Code is working on time-consuming tasks like code generation or refactoring, you might miss when it finishes if you're doing something else. This hook:

1. Records the timestamp when you submit a prompt
2. Plays a sound when the agent finishes responding, if enough time has elapsed

Short responses (under 60 seconds) won't trigger a notification.

## Multiple Session Support

The state file uses a dict keyed by session ID, so multiple concurrent Claude Code sessions each get independent notifications.

## Agent Teams Support

When using Agent Teams, the Stop hook fires on the leader session every time a teammate completes. This hook **correctly filters intermediate Stops during team work** and only notifies after the final response once the team is disbanded.

### 3-Layer Filter

| # | Filter | Purpose |
|---|--------|---------|
| 1 | session_id match | Exclude team member Stops |
| 2 | Elapsed time > 60s | Exclude short responses |
| 3 | teams/ leadSessionId check | Exclude intermediate Stops during team work |

```
UserPromptSubmit
  → Add {session_id: timestamp} to state dict

Stop
  → session_id in state? → No → exit (team member etc.)
  → 60s elapsed? → No → exit (short response)
  → Active team in teams/? → Yes → exit (team work in progress)
  → Remove entry from state → Play sound 🔔
```

## Installation

### 1. Copy hook scripts

```bash
mkdir -p ~/.claude/hooks
cp hooks/notify_prompt_submit.py ~/.claude/hooks/
cp hooks/notify_stop.py ~/.claude/hooks/
```

Windows:
```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\hooks"
Copy-Item hooks\notify_prompt_submit.py "$env:USERPROFILE\.claude\hooks\"
Copy-Item hooks\notify_stop.py "$env:USERPROFILE\.claude\hooks\"
```

### 2. Customize notification sound

Edit the `notify()` function in `notify_stop.py` to use your preferred notification method.

Default is Windows system sound (`Windows Notify Calendar.wav`).

macOS:
```python
def notify():
    subprocess.Popen(["afplay", "/System/Library/Sounds/Glass.aiff"])
```

Linux:
```python
def notify():
    subprocess.Popen(["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"])
```

### 3. Add hook configuration

Add the following to `~/.claude/settings.json` (merge with existing `hooks` section if present):

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python -X utf8 ~/.claude/hooks/notify_prompt_submit.py"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python -X utf8 ~/.claude/hooks/notify_stop.py"
          }
        ]
      }
    ]
  }
}
```

**Windows**: Replace paths with full paths:
```json
"command": "python -X utf8 C:\\Users\\YourName\\.claude\\hooks\\notify_prompt_submit.py"
"command": "python -X utf8 C:\\Users\\YourName\\.claude\\hooks\\notify_stop.py"
```

### 4. Requirements

- Python 3.10+ (standard library only)

### 5. Adjust threshold

Change `THRESHOLD_SECONDS` in `notify_stop.py` (default: 60 seconds).

## File Structure

| File | Role |
|------|------|
| `hooks/notify_prompt_submit.py` | Records session_id + timestamp on UserPromptSubmit |
| `hooks/notify_stop.py` | 3-layer filter + notification on Stop |
| `settings.example.json` | Example hook configuration |

## Cost

- API cost: Zero (standard library only, no external API calls)
- Execution time: Milliseconds per invocation. Exits immediately if conditions aren't met
- Side effects: Creates one file `~/.claude/hooks/.notify_state.json` (a few dozen bytes)

## License

MIT
