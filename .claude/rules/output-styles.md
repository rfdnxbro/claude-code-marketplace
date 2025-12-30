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
| `description` | - | `/output-style` UIで表示される説明文 | なし |
| `keep-coding-instructions` | - | コーディング関連のシステムプロンプトを保持するか | `false` |

## ビルトインスタイル

| スタイル | 説明 |
|---------|------|
| `default` | ソフトウェアエンジニアリング作業に最適化された標準スタイル |
| `explanatory` | 教育的な「Insights」を提供しながらコーディングをサポート |
| `learning` | 協調的な学習モード。`TODO(human)` マーカーでユーザーに実装を促す |

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

```bash
# メニューから選択
/output-style

# 直接指定
/output-style explanatory
/output-style learning
/output-style [custom-style-name]
```

## 設定ファイル

設定は `.claude/settings.local.json` に保存される：

```json
{
  "outputStyle": "explanatory"
}
```

## 動作の仕組み

- 出力スタイルはシステムプロンプトを直接変更する
- すべてのスタイルで効率的な出力用の指示が除外される
- カスタムスタイルではコーディング関連の指示も除外される（`keep-coding-instructions: true` で保持可能）

## CLAUDE.mdとの違い

| 観点 | Output Styles | CLAUDE.md |
|-----|---------------|-----------|
| 適用方法 | システムプロンプトを置換 | ユーザーメッセージとして追加 |
| デフォルト指示 | 除外される | 保持される |
| 用途 | 根本的な動作変更 | 追加の指示・コンテキスト |
