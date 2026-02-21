# claude-code-task-done-notify

Claude Code の長時間タスクが完了したとき、音で通知してくれるフック。

[English](README.en.md)

## これは何？

Claude Code でコード生成やリファクタリングなど時間のかかるタスクを実行中、完了を待つ間に別の作業をしていると終わったことに気づけません。このフックは：

1. ユーザーがプロンプトを送った時刻を記録
2. エージェントの応答完了時に、一定時間以上経過していれば音で通知

短い応答（60秒未満）では鳴りません。

## Agent Teams 対応

Agent Teams 使用時、チームメンバーの完了報告のたびにリーダーセッションで Stop hook が発火しますが、このフックは **チーム作業中の中間 Stop を正しくフィルタ** します。チーム解散後の最終応答でのみ通知します。

### 3層フィルタ

| # | フィルタ | 目的 |
|---|---------|------|
| 1 | session_id 照合 | チームメンバーの Stop を除外 |
| 2 | 経過時間 > 60秒 | 短い応答を除外 |
| 3 | teams/ の leadSessionId チェック | チーム作業中の中間 Stop を除外 |

```
UserPromptSubmit
  → session_id + timestamp を保存

Stop
  → session_id 一致？ → No → exit（チームメンバー）
  → 60秒経過？ → No → exit（短い応答）
  → teams/ に自分のチームがある？ → Yes → exit（チーム作業中）
  → 通知音 🔔
```

## インストール

### 1. フックスクリプトをコピー

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

### 2. 通知音をカスタマイズ

`notify_stop.py` の `notify()` 関数を編集して、好みの通知方法に変更できます。

デフォルトは Windows のシステムサウンド（`Windows Notify Calendar.wav`）です。

macOS の場合：
```python
def notify():
    subprocess.Popen(["afplay", "/System/Library/Sounds/Glass.aiff"])
```

Linux の場合：
```python
def notify():
    subprocess.Popen(["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"])
```

### 3. フック設定を追加

`~/.claude/settings.json` に以下を追加（既存の `hooks` セクションがある場合はマージ）：

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

**Windows**: パスをフルパスに置き換えてください：
```json
"command": "python -X utf8 C:\\Users\\YourName\\.claude\\hooks\\notify_prompt_submit.py"
"command": "python -X utf8 C:\\Users\\YourName\\.claude\\hooks\\notify_stop.py"
```

### 4. 要件

- Python 3.10+（標準ライブラリのみ）

### 5. 閾値の変更

`notify_stop.py` の `THRESHOLD_SECONDS` を変更してください（デフォルト: 60秒）。

## ファイル構成

| ファイル | 役割 |
|---------|------|
| `hooks/notify_prompt_submit.py` | UserPromptSubmit で session_id + タイムスタンプを記録 |
| `hooks/notify_stop.py` | Stop で3層フィルタ + 通知 |
| `settings.example.json` | フック設定のサンプル |

## コスト

- API コスト: ゼロ（標準ライブラリのみ、外部 API 呼び出しなし）
- 実行時間: 毎回数ミリ秒。条件を満たさなければ即終了
- 副作用: `~/.claude/hooks/.notify_state.json`（数十バイト）を1ファイル作成

## ライセンス

MIT
