---
paths: .claude/settings.local.json, .claude/settings.json
---

# ステータスライン設定

ステータスラインはClaude Codeのターミナル下部に表示される情報バーです。カスタムスクリプトを使用して、コンテキスト情報を表示するようカスタマイズできます。

## 設定方法

### 方法1: `/statusline` コマンド（推奨）

```text
/statusline
```

Claude Codeがカスタムステータスラインの設定を支援します。

```text
/statusline show the model name in orange
```

のように希望する動作を伝えることも可能です。

### 方法2: 直接設定

`.claude/settings.json` または `.claude/settings.local.json` に `statusLine` を追加:

```json
{
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline.sh",
    "padding": 0,
    "refreshInterval": 5
  }
}
```

| オプション | 必須 | 説明 |
|-----------|------|------|
| `type` | Yes | `"command"` を指定 |
| `command` | Yes | 実行するスクリプトのパス（`~` 展開対応） |
| `padding` | No | 左側のパディング（`0` で端まで表示） |
| `refreshInterval` | No | N秒ごとにステータスラインコマンドを再実行する間隔（秒）（v2.1.97以降） |

**ファイルの使い分け**:

- `.claude/settings.json`: プロジェクト全体で共有する設定（バージョン管理にコミット）
- `.claude/settings.local.json`: 個人用設定（`.gitignore`に追加推奨）

## 仕組み

- ステータスラインは会話メッセージが更新されるときに更新される
- 更新は最大300msごとに実行される
- `refreshInterval` を設定した場合、指定した秒数ごとにコマンドが再実行される（v2.1.97以降）
- コマンドのstdoutの最初の行がステータスラインテキストになる
- ANSIカラーコードがサポートされている
- Claude Codeは現在のセッションに関するコンテキスト情報をJSON形式でstdin経由でスクリプトに渡す

## JSON入力構造

ステータスラインスクリプトはstdin経由で以下のJSON形式のデータを受け取ります:

```json
{
  "hook_event_name": "Status",
  "session_id": "abc123...",
  "transcript_path": "/path/to/transcript.json",
  "cwd": "/current/working/directory",
  "model": {
    "id": "claude-opus-4-1",
    "display_name": "Opus"
  },
  "workspace": {
    "current_dir": "/current/working/directory",
    "project_dir": "/original/project/directory",
    "added_dirs": ["/additional/directory1", "/additional/directory2"],
    "git_worktree": "/path/to/linked/worktree"
  },
  "worktree": {
    "name": "my-worktree",
    "path": "/path/to/worktree",
    "branch": "feature/my-feature",
    "originalRepoDir": "/path/to/original/repo"
  },
  "version": "1.0.80",
  "output_style": {
    "name": "default"
  },
  "cost": {
    "total_cost_usd": 0.01234,
    "total_duration_ms": 45000,
    "total_api_duration_ms": 2300,
    "total_lines_added": 156,
    "total_lines_removed": 23
  },
  "context_window": {
    "total_input_tokens": 15234,
    "total_output_tokens": 4521,
    "context_window_size": 200000,
    "used_percentage": 22.5,
    "remaining_percentage": 77.5,
    "current_usage": {
      "input_tokens": 8500,
      "output_tokens": 1200,
      "cache_creation_input_tokens": 5000,
      "cache_read_input_tokens": 2000
    }
  },
  "rate_limits": {
    "5h": {
      "used_percentage": 42.5,
      "resets_at": "2026-03-20T15:30:00Z"
    },
    "7d": {
      "used_percentage": 18.0,
      "resets_at": "2026-03-27T00:00:00Z"
    }
  },
  "effort": {
    "level": "medium"
  },
  "thinking": {
    "enabled": false
  }
}
```

### 利用可能なフィールド

#### モデル情報

| フィールド | 型 | 説明 | 例 |
|-----------|---|------|-----|
| `model.id` | string | モデルID | `claude-opus-4-1` |
| `model.display_name` | string | 表示名 | `Opus` |

#### ワークスペース情報

| フィールド | 型 | 説明 | 例 |
|-----------|---|------|-----|
| `workspace.current_dir` | string | 現在のディレクトリ | `/home/user/project` |
| `workspace.project_dir` | string | プロジェクトディレクトリ | `/home/user/project` |
| `workspace.added_dirs` | array | `/add-dir` で追加したディレクトリ一覧（v2.1.47以降） | `["/extra/dir"]` |
| `workspace.git_worktree` | string | 現在のディレクトリがリンクされたgit worktree内にある場合に設定される（v2.1.97以降）。それ以外は存在しない | `/path/to/linked/worktree` |
| `cwd` | string | 現在のワーキングディレクトリ | `/home/user/project` |

#### Worktree情報（v2.1.64以降）

`--worktree` セッションで実行中の場合のみ存在するフィールドです。それ以外の場合は `worktree` フィールド自体が存在しません。

> **注意**: `workspace.git_worktree`（v2.1.97以降）とは異なります。`worktree` は `--worktree` フラグで起動したセッション専用のフィールドで、セッション管理情報を含みます。`workspace.git_worktree` は通常セッションでも現在のディレクトリがリンクされたgit worktree内にある場合に設定されます。

| フィールド | 型 | 説明 | 例 |
|-----------|---|------|-----|
| `worktree.name` | string | Worktree名 | `my-worktree` |
| `worktree.path` | string | Worktreeのパス | `/path/to/worktree` |
| `worktree.branch` | string | Worktreeのブランチ名 | `feature/my-feature` |
| `worktree.originalRepoDir` | string | 元のリポジトリディレクトリ | `/path/to/original/repo` |

#### セッション情報

| フィールド | 型 | 説明 | 例 |
|-----------|---|------|-----|
| `version` | string | Claude Codeのバージョン | `1.0.80` |
| `session_id` | string | セッションID | `abc123...` |
| `output_style.name` | string | 出力スタイル名 | `default` |
| `effort.level` | string | 現在の effort レベル（v2.1.119以降） | `low`, `medium`, `high`, `max` |
| `thinking.enabled` | boolean | 思考（thinking）機能が有効かどうか（v2.1.119以降） | `false` |

#### コスト情報

| フィールド | 型 | 説明 | 例 |
|-----------|---|------|-----|
| `cost.total_cost_usd` | number | 累計コスト（USD） | `0.01234` |
| `cost.total_duration_ms` | number | 累計時間（ms） | `45000` |
| `cost.total_api_duration_ms` | number | API呼び出し時間（ms） | `2300` |
| `cost.total_lines_added` | number | 追加行数 | `156` |
| `cost.total_lines_removed` | number | 削除行数 | `23` |

#### コンテキストウィンドウ情報

| フィールド | 型 | 説明 | 例 |
|-----------|---|------|-----|
| `context_window.context_window_size` | number | 最大トークン数 | `200000` |
| `context_window.total_input_tokens` | number | 累計入力トークン | `15234` |
| `context_window.total_output_tokens` | number | 累計出力トークン | `4521` |
| `context_window.used_percentage` | number | 使用率（%） | `22.5` |
| `context_window.remaining_percentage` | number | 残り率（%） | `77.5` |
| `context_window.current_usage` | object | 現在の使用状況（`null`の可能性あり） | - |

`current_usage`オブジェクト（存在する場合）:

| フィールド | 型 | 説明 | 例 |
|-----------|---|------|-----|
| `input_tokens` | number | 現在の入力トークン | `8500` |
| `output_tokens` | number | 現在の出力トークン | `1200` |
| `cache_creation_input_tokens` | number | キャッシュ作成トークン | `5000` |
| `cache_read_input_tokens` | number | キャッシュ読み取りトークン | `2000` |

#### レート制限情報（v2.1.80以降）

Claude.ai のレート制限使用状況を表示します。存在しない場合は `rate_limits` フィールド自体が省略されます。

| フィールド | 型 | 説明 | 例 |
|-----------|---|------|-----|
| `rate_limits.5h.used_percentage` | number | 5時間ウィンドウの使用率（%） | `42.5` |
| `rate_limits.5h.resets_at` | string | 5時間ウィンドウのリセット日時（ISO 8601） | `"2026-03-20T15:30:00Z"` |
| `rate_limits.7d.used_percentage` | number | 7日間ウィンドウの使用率（%） | `18.0` |
| `rate_limits.7d.resets_at` | string | 7日間ウィンドウのリセット日時（ISO 8601） | `"2026-03-27T00:00:00Z"` |

## スクリプト例

### シンプルなステータスライン

```bash
#!/bin/bash
# stdinからJSON入力を読み取る
input=$(cat)

# jqで値を抽出
MODEL_DISPLAY=$(echo "$input" | jq -r '.model.display_name')
CURRENT_DIR=$(echo "$input" | jq -r '.workspace.current_dir')

echo "[$MODEL_DISPLAY] ${CURRENT_DIR##*/}"
```

### Git対応ステータスライン

```bash
#!/bin/bash
input=$(cat)

MODEL_DISPLAY=$(echo "$input" | jq -r '.model.display_name')
CURRENT_DIR=$(echo "$input" | jq -r '.workspace.current_dir')

# Gitリポジトリ内ならブランチ名を表示
GIT_BRANCH=""
if git rev-parse --git-dir > /dev/null 2>&1; then
    BRANCH=$(git branch --show-current 2>/dev/null)
    if [ -n "$BRANCH" ]; then
        GIT_BRANCH=" | 🌿 $BRANCH"
    fi
fi

echo "[$MODEL_DISPLAY] 📁 ${CURRENT_DIR##*/}$GIT_BRANCH"
```

### コンテキスト使用率表示

```bash
#!/bin/bash
input=$(cat)

MODEL=$(echo "$input" | jq -r '.model.display_name')
CONTEXT_SIZE=$(echo "$input" | jq -r '.context_window.context_window_size')
USAGE=$(echo "$input" | jq '.context_window.current_usage')

if [ "$USAGE" != "null" ]; then
    # current_usageフィールドからコンテキスト使用率を計算
    CURRENT_TOKENS=$(echo "$USAGE" | jq '.input_tokens + .cache_creation_input_tokens + .cache_read_input_tokens')
    PERCENT_USED=$((CURRENT_TOKENS * 100 / CONTEXT_SIZE))
    echo "[$MODEL] Context: ${PERCENT_USED}%"
else
    echo "[$MODEL] Context: 0%"
fi
```

### ANSIカラー付きステータスライン

```bash
#!/bin/bash
input=$(cat)

# ANSIカラーコード
CYAN='\033[36m'
YELLOW='\033[33m'
RED='\033[31m'
GREEN='\033[32m'
MAGENTA='\033[35m'
RESET='\033[0m'

# 値を抽出
MODEL=$(echo "$input" | jq -r '.model.display_name // "Unknown"')
COST=$(echo "$input" | jq -r '.cost.total_cost_usd // 0')
COST_FORMATTED=$(printf "%.2f" "$COST")

# コンテキスト使用率
CONTEXT_SIZE=$(echo "$input" | jq -r '.context_window.context_window_size // 200000')
USAGE=$(echo "$input" | jq '.context_window.current_usage')
if [ "$USAGE" != "null" ] && [ -n "$USAGE" ]; then
    CURRENT_TOKENS=$(echo "$USAGE" | jq '.input_tokens + .cache_creation_input_tokens + .cache_read_input_tokens')
    PERCENT_USED=$((CURRENT_TOKENS * 100 / CONTEXT_SIZE))
else
    PERCENT_USED=0
fi

# 使用率に応じて色を変更（70%以上で赤）
if [ "$PERCENT_USED" -ge 70 ]; then
    PERCENT_COLOR=$RED
else
    PERCENT_COLOR=$YELLOW
fi

# Gitブランチ
GIT_BRANCH=""
if git rev-parse --git-dir > /dev/null 2>&1; then
    BRANCH=$(git branch --show-current 2>/dev/null)
    if [ -n "$BRANCH" ]; then
        GIT_BRANCH=" | ${MAGENTA}🌿 ${BRANCH}${RESET}"
    fi
fi

echo -e "[${CYAN}${MODEL}${RESET}] ${PERCENT_COLOR}📊 ${PERCENT_USED}%${RESET} | ${GREEN}💰 \$${COST_FORMATTED}${RESET}${GIT_BRANCH}"
```

### Python例

```python
#!/usr/bin/env python3
import json
import sys
import os

# stdinからJSONを読み取る
data = json.load(sys.stdin)

# 値を抽出
model = data['model']['display_name']
current_dir = os.path.basename(data['workspace']['current_dir'])

# Gitブランチを確認
git_branch = ""
if os.path.exists('.git'):
    try:
        with open('.git/HEAD', 'r') as f:
            ref = f.read().strip()
            if ref.startswith('ref: refs/heads/'):
                git_branch = f" | 🌿 {ref.replace('ref: refs/heads/', '')}"
    except:
        pass

print(f"[{model}] 📁 {current_dir}{git_branch}")
```

### Node.js例

```javascript
#!/usr/bin/env node
const { readFileSync } = require('fs');
const path = require('path');

// stdinからJSONを読み取る
let input = '';
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
    const data = JSON.parse(input);

    // 値を抽出
    const model = data.model.display_name;
    const currentDir = path.basename(data.workspace.current_dir);

    // Gitブランチを確認
    let gitBranch = '';
    try {
        const headContent = readFileSync('.git/HEAD', 'utf8').trim();
        if (headContent.startsWith('ref: refs/heads/')) {
            gitBranch = ` | 🌿 ${headContent.replace('ref: refs/heads/', '')}`;
        }
    } catch {
        // Gitリポジトリでない
    }

    console.log(`[${model}] 📁 ${currentDir}${gitBranch}`);
});
```

## ベストプラクティス

**簡潔に**: ステータスラインは1行に収まるべき。最も重要な情報に絞る。

**視認性**: 絵文字（ターミナルがサポートしている場合）とANSIカラーコードを使用して、情報をスキャンしやすくする。

**jqを使用**: BashでのJSON解析には`jq`コマンドを使用する。

**テスト**: モックJSON入力を使用して手動でスクリプトをテストする:

```bash
echo '{"model":{"display_name":"Test"},"workspace":{"current_dir":"/test"}}' | ./statusline.sh
```

**パフォーマンス**: 必要に応じて、高コストの操作（gitステータスなど）をキャッシュすることを検討する。

## トラブルシューティング

- **ステータスラインが表示されない**: スクリプトが実行可能か確認（`chmod +x`）
- **出力が表示されない**: スクリプトがstdoutに出力していることを確認（stderrではなく）
- **エラーが発生する**: `jq`がインストールされているか確認

## 関連ドキュメント

- [plugin-manifest.md](plugin-manifest.md): プラグインマニフェストの仕様
- [output-styles.md](output-styles.md): 出力スタイルのカスタマイズ
