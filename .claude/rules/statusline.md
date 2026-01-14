---
paths: .claude/settings.local.json, .claude/settings.json
---

# ステータスライン設定

ステータスラインはClaude Codeのターミナル下部に表示される情報バーです。プロジェクト固有の情報を表示するようカスタマイズできます。

## 設定ファイル

ステータスラインの設定は`.claude/settings.local.json`または`.claude/settings.json`で行います:

```json
{
  "status.line": "{{ context_window.used_tokens }}/{{ context_window.max_tokens }} tokens ({{ context_window.used_percentage }}%)"
}
```

**ファイルの使い分け**:

- `.claude/settings.json`: プロジェクト全体で共有する設定（バージョン管理にコミット）
- `.claude/settings.local.json`: 個人用設定（`.gitignore`に追加推奨）

## 利用可能なフィールド

### コンテキストウィンドウ

| フィールド | 型 | 説明 | 例 | バージョン |
|-----------|---|------|-----|-----------|
| `context_window.used_tokens` | number | 使用済みトークン数 | `45000` | - |
| `context_window.max_tokens` | number | 最大トークン数 | `200000` | - |
| `context_window.remaining_tokens` | number | 残りトークン数 | `155000` | - |
| `context_window.used_percentage` | number | 使用率（%、小数点以下1桁） | `22.5` | v2.1.6+ |
| `context_window.remaining_percentage` | number | 残り率（%、小数点以下1桁） | `77.5` | v2.1.6+ |

**バージョン情報**:

- `used_percentage`と`remaining_percentage`はv2.1.6で追加されました
- v2.1.5以前のバージョンでは手動計算が必要: `{{ (context_window.used_tokens / context_window.max_tokens * 100) | round(1) }}`

### プロジェクト情報

| フィールド | 型 | 説明 | 例 |
|-----------|---|------|-----|
| `project.name` | string | プロジェクト名 | `my-project` |
| `project.path` | string | プロジェクトの絶対パス | `/home/user/my-project` |

### Git情報

| フィールド | 型 | 説明 | 例 |
|-----------|---|------|-----|
| `git.branch` | string | 現在のブランチ名 | `main` |
| `git.status` | string | Gitステータス概要 | `modified: 3` |

## テンプレート構文

ステータスラインは[Liquid](https://shopify.github.io/liquid/)テンプレート構文を使用します。

### 基本的な変数展開

```liquid
{{ variable_name }}
```

### 条件分岐

```liquid
{% if git.branch %}
  Branch: {{ git.branch }}
{% else %}
  No Git repository
{% endif %}
```

### フィルター

```liquid
{{ context_window.used_percentage | round(1) }}%
```

利用可能なフィルター:

- `round(n)`: 小数点以下n桁に丸める
- `upcase`: 大文字に変換
- `downcase`: 小文字に変換
- `truncate(n)`: n文字に切り詰め

## サンプル設定

### シンプルなトークンカウンター

```json
{
  "status.line": "{{ context_window.used_tokens }}/{{ context_window.max_tokens }}"
}
```

表示例: `45000/200000`

### パーセンテージ表示（v2.1.6以降）

```json
{
  "status.line": "Context: {{ context_window.used_percentage }}% used"
}
```

表示例: `Context: 22.5% used`

### 残り容量表示

```json
{
  "status.line": "{{ context_window.remaining_percentage }}% remaining"
}
```

表示例: `77.5% remaining`

### プログレスバー風

```json
{
  "status.line": "[{% for i in (1..10) %}{% if i <= (context_window.used_percentage / 10) %}█{% else %}░{% endif %}{% endfor %}] {{ context_window.used_percentage }}%"
}
```

表示例: `[██░░░░░░░░] 22.5%`

### Git情報付き

```json
{
  "status.line": "{{ git.branch }} | {{ context_window.used_tokens }}/{{ context_window.max_tokens }} tokens"
}
```

表示例: `main | 45000/200000 tokens`

### 複合情報

```json
{
  "status.line": "{{ project.name }} [{{ git.branch }}] | Tokens: {{ context_window.used_percentage }}% ({{ context_window.remaining_tokens }} remaining)"
}
```

表示例: `my-project [main] | Tokens: 22.5% (155000 remaining)`

## ベストプラクティス

**簡潔に**: ステータスラインは限られたスペースしかない。最も重要な情報に絞る。

**パーセンテージを活用**: 絶対値よりも相対的な使用率の方が直感的（v2.1.6以降は`used_percentage`/`remaining_percentage`を使用）。

**条件分岐で柔軟に**: Gitリポジトリがない環境でも動作するよう、条件分岐を活用。

**視認性**: 絵文字やUnicode文字（█, ░等）を使用して視覚的に分かりやすく。

## 注意事項

- ステータスラインの更新頻度は自動的に制御される（パフォーマンス最適化のため）
- 非常に長い文字列はターミナル幅に応じて切り詰められる
- テンプレート構文エラーがある場合、ステータスラインは表示されない

## 関連ドキュメント

- [plugin-manifest.md](plugin-manifest.md): プラグインマニフェストの仕様
- [output-styles.md](output-styles.md): 出力スタイルのカスタマイズ
