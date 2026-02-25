"""Background monitor: wait for jsonl to stop growing, then notify.

Usage: notify_monitor.py <transcript_path> <idle_seconds> <wav_path> <session_id> [elapsed] [threshold]

Spawned by notify_stop.py after filters 1-2 pass.
Checks if the transcript jsonl is still being written to (= agent still working).
If file size is unchanged after idle_seconds, agent is done → play sound.
"""
import sys
import os
import time
import subprocess


def main():
    if len(sys.argv) < 5:
        sys.exit(1)

    transcript_path = sys.argv[1]
    idle_seconds = float(sys.argv[2])
    wav_path = sys.argv[3]
    session_id = sys.argv[4]
    elapsed = float(sys.argv[5]) if len(sys.argv) > 5 else 0
    threshold = float(sys.argv[6]) if len(sys.argv) > 6 else 60

    if not transcript_path or not os.path.exists(transcript_path):
        notify(wav_path, elapsed, threshold)
        return

    while True:
        if not os.path.exists(transcript_path):
            return

        size_before = os.path.getsize(transcript_path)
        time.sleep(idle_seconds)

        if not os.path.exists(transcript_path):
            return

        size_after = os.path.getsize(transcript_path)

        if size_after == size_before:
            notify(wav_path, elapsed, threshold)
            return


def notify(wav_path, elapsed, threshold):
    """Play notification sound if elapsed time exceeds threshold."""
    if elapsed < threshold:
        return

    # Windows
    if os.name == "nt":
        try:
            subprocess.Popen(
                ["powershell", "-NoProfile", "-Command",
                 f'(New-Object System.Media.SoundPlayer "{wav_path}").PlaySync()'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass
    # macOS
    elif sys.platform == "darwin":
        try:
            subprocess.Popen(
                ["afplay", "/System/Library/Sounds/Glass.aiff"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass
    # Linux
    else:
        try:
            subprocess.Popen(
                ["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass


if __name__ == "__main__":
    main()
