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
| 2 | teams/ leadSessionId check | Exclude intermediate Stops during team work |
| 3 | jsonl idle check | Exclude intermediate Stops while agent is still responding |

```
UserPromptSubmit
  → Add {session_id: timestamp} to state dict

Stop
  → session_id in state? → No → exit (team member etc.)
  → Active team in teams/? → Yes → exit (team work in progress)
  → Remove entry from state
  → Spawn background monitor
    → jsonl still growing? → Wait (agent still working)
    → jsonl idle + 60s elapsed → Play sound 🔔
```

## Installation

### 1. Copy hook scripts

```bash
mkdir -p ~/.claude/hooks
cp hooks/notify_prompt_submit.py ~/.claude/hooks/
cp hooks/notify_stop.py ~/.claude/hooks/
cp hooks/notify_monitor.py ~/.claude/hooks/
```

Windows:
```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\hooks"
Copy-Item hooks\notify_prompt_submit.py "$env:USERPROFILE\.claude\hooks\"
Copy-Item hooks\notify_stop.py "$env:USERPROFILE\.claude\hooks\"
Copy-Item hooks\notify_monitor.py "$env:USERPROFILE\.claude\hooks\"
```

### 2. Customize notification sound

Edit `WAV_PATH` in `notify_stop.py` to use your preferred sound file.

`notify_monitor.py` has cross-platform notification built in:
- **Windows**: PowerShell SoundPlayer (default: `Windows Notify Calendar.wav`)
- **macOS**: `afplay` (`Glass.aiff`)
- **Linux**: `paplay` (freedesktop completion sound)

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

### 5. Adjust thresholds

Change these in `notify_stop.py`:

| Variable | Default | Description |
|----------|---------|-------------|
| `THRESHOLD_SECONDS` | 60 | No notification for responses shorter than this |
| `IDLE_SECONDS` | 3 | Seconds of jsonl inactivity before considering agent idle |

## File Structure

| File | Role |
|------|------|
| `hooks/notify_prompt_submit.py` | Records session_id + timestamp on UserPromptSubmit |
| `hooks/notify_stop.py` | 3-layer filter + spawn background monitor on Stop |
| `hooks/notify_monitor.py` | jsonl idle detection + sound notification |
| `settings.example.json` | Example hook configuration |

## Cost

- API cost: Zero (standard library only, no external API calls)
- Execution time: Milliseconds per invocation. Exits immediately if conditions aren't met
- Side effects: Creates one file `~/.claude/hooks/.notify_state.json` (a few dozen bytes)

## License

MIT
