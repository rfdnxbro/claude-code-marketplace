---
paths: plugins/*/.claude/output-styles/*.md, .claude/output-styles/*.md
---

# 出力スタイル

Markdown形式で記述します。配置場所はプラグインルートの `.claude/output-styles/` ディレクトリ。

## 形式

```markdown
---
name: My Custom Style
description: スタイルの説明（UIに表示される）
keep-coding-instructions: false
---

# カスタムスタイルの指示

ここにスタイル固有の指示を記述...
```

## フロントマター仕様

| フィールド | 必須 | 説明 | デフォルト |
|-----------|:---:|------|-----------|
| `name` | - | スタイルの表示名 | ファイル名から自動取得 |
| `description` | - | `/config` の選択メニューで表示される説明文 | なし |
| `keep-coding-instructions` | - | Claude Code組み込みのソフトウェアエンジニアリング指示を保持するか | `false` |
| `force-for-plugin` | - | プラグイン出力スタイル専用。プラグイン有効化時にユーザー選択なしで自動適用し、ユーザーの `outputStyle` 設定を上書きする。複数の有効プラグインが指定した場合は最初に読み込まれたものが使われる | `false` |

## ビルトインスタイル

| スタイル | 説明 |
|---------|------|
| `Default` | ソフトウェアエンジニアリング作業に最適化された標準スタイル |
| `Proactive` | 即座に実行し、定型的な判断では立ち止まらず合理的な仮定を置き、計画より行動を優先する。auto modeより強い自律実行ガイダンスだが、permission modeは変えないためツール実行前のパーミッションプロンプトは引き続き表示される |
| `Explanatory` | 教育的な「Insights」を提供しながらコーディングをサポート |
| `Learning` | 協調的な学習モード。`TODO(human)` マーカーでユーザーに実装を促す |

## サンプル

### 教育用スタイル

```markdown
---
name: teaching-mode
description: コーディング中に概念を説明する
keep-coding-instructions: true
---

# Teaching Mode

実装時に以下を詳しく説明してください：
- アーキテクチャ上の決定理由
- ソフトウェアエンジニアリングのベストプラクティスとの関連
- 開発者にとっての学習ポイント
```

### データ分析スタイル

```markdown
---
name: data-analysis
description: データ分析タスクに最適化
keep-coding-instructions: false
---

# Data Analysis Mode

データ分析アシスタントとして動作します：
- 明確なデータインサイトと可視化
- 統計的な厳密性
- 発見事項のナラティブな説明
```

## 使用方法

> **削除済み**: スタンドアロンの `/output-style` コマンドは廃止されました。`/config` コマンドを使うか、`outputStyle` 設定を直接編集してください。

```bash
# /config の「Output style」から選択
/config
```

設定ファイルで直接指定することもできます（後述の「設定ファイル」を参照）。

## セッション開始時のスタイル固定

出力スタイルはセッション開始時に固定されます。これによりプロンプトキャッシングの効率が最適化されます。

- セッション開始後に `/config` でスタイルを変更しても、現在のセッションには反映されません（`/clear` または次回セッションで有効）
- 変更は次回のセッション開始時に有効になります

## 設定ファイル

設定は `.claude/settings.local.json` に保存される：

```json
{
  "outputStyle": "Explanatory"
}
```

## 動作の仕組み

- 出力スタイルはシステムプロンプトを直接変更する
- スタイルはセッション開始時に固定される
- すべてのスタイルは独自の指示をシステムプロンプト末尾に追加し、会話中にスタイル遵守のリマインダーを発生させる
- カスタムスタイルはClaude Code組み込みのソフトウェアエンジニアリング指示（変更スコープ・コメントの書き方・検証方法など）を除外する（`keep-coding-instructions: true` で保持可能）

## CLAUDE.mdとの違い

| 観点 | Output Styles | CLAUDE.md |
|-----|---------------|-----------|
| 適用方法 | システムプロンプトを置換 | ユーザーメッセージとして追加 |
| デフォルト指示 | 除外される | 保持される |
| 用途 | 根本的な動作変更 | 追加の指示・コンテキスト |
