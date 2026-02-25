# claude-code-task-done-notify

Claude Code の長時間タスクが完了したとき、音で通知してくれるフック。

[English](README.en.md)

## これは何？

Claude Code でコード生成やリファクタリングなど時間のかかるタスクを実行中、完了を待つ間に別の作業をしていると終わったことに気づけません。このフックは：

1. ユーザーがプロンプトを送った時刻を記録
2. エージェントの応答完了時に、一定時間以上経過していれば音で通知

短い応答（60秒未満）では鳴りません。

## 複数セッション対応

状態ファイルはセッションIDをキーとした dict で管理されるため、複数の Claude Code セッションを同時に実行しても各セッションが独立して通知されます。

## Agent Teams 対応

Agent Teams 使用時、チームメンバーの完了報告のたびにリーダーセッションで Stop hook が発火しますが、このフックは **チーム作業中の中間 Stop を正しくフィルタ** します。チーム解散後の最終応答でのみ通知します。

### 3層フィルタ

| # | フィルタ | 目的 |
|---|---------|------|
| 1 | session_id 照合 | チームメンバーの Stop を除外 |
| 2 | teams/ の leadSessionId チェック | チーム作業中の中間 Stop を除外 |
| 3 | jsonl idle チェック | エージェントがまだ応答中の中間 Stop を除外 |

```
UserPromptSubmit
  → state dict に {session_id: timestamp} を追加

Stop
  → session_id が state に存在？ → No → exit（チームメンバー等）
  → teams/ に自分のチームがある？ → Yes → exit（チーム作業中）
  → state からエントリ削除
  → バックグラウンドモニター起動
    → jsonl が成長中？ → 待機（エージェントまだ作業中）
    → jsonl が静止 + 60秒以上経過 → 通知音 🔔
```

## インストール

### 1. フックスクリプトをコピー

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

### 2. 通知音をカスタマイズ

`notify_stop.py` の `WAV_PATH` を編集して、好みのサウンドファイルに変更できます。

`notify_monitor.py` にはクロスプラットフォームの通知が組み込まれています：
- **Windows**: PowerShell の SoundPlayer（デフォルト: `Windows Notify Calendar.wav`）
- **macOS**: `afplay`（`Glass.aiff`）
- **Linux**: `paplay`（freedesktop の完了音）

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

`notify_stop.py` の以下を変更してください：

| 変数 | デフォルト | 説明 |
|------|-----------|------|
| `THRESHOLD_SECONDS` | 60 | この秒数未満の応答では通知しない |
| `IDLE_SECONDS` | 3 | jsonl が静止したと判断するまでの秒数 |

## ファイル構成

| ファイル | 役割 |
|---------|------|
| `hooks/notify_prompt_submit.py` | UserPromptSubmit で session_id + タイムスタンプを記録 |
| `hooks/notify_stop.py` | Stop で3層フィルタ + バックグラウンドモニター起動 |
| `hooks/notify_monitor.py` | jsonl idle 検知 + 通知音再生 |
| `settings.example.json` | フック設定のサンプル |

## コスト

- API コスト: ゼロ（標準ライブラリのみ、外部 API 呼び出しなし）
- 実行時間: 毎回数ミリ秒。条件を満たさなければ即終了
- 副作用: `~/.claude/hooks/.notify_state.json`（数十バイト）を1ファイル作成

## ライセンス

MIT
