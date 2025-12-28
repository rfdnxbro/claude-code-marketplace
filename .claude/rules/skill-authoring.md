---
paths: plugins/*/skills/**/SKILL.md, .claude/skills/**/SKILL.md
---

# スキル作成ベストプラクティス

## Frontmatter

```yaml
---
name: processing-something
description: XとYを処理する。ユーザーがZについて言及した時やWが必要な時に使用。
---
```

**name**:
- 最大64文字
- 小文字、数字、ハイフンのみ
- 動名詞形を推奨（`processing-pdfs`、`pdf-processor`ではない）
- 予約語禁止: `anthropic`, `claude`

**description**:
- 最大1024文字
- 三人称で記述（「ファイルを処理する」、「私がファイルを処理します」ではない）
- 何をするか AND いつ使うかを含める
- 発見性のため具体的なキーワードを含める

## ディレクトリ構造

スキルはSKILL.mdを中心に、必要に応じてサポートファイルを配置:

```
my-skill/
├── SKILL.md           # 必須: エントリーポイント
├── reference.md       # オプション: 詳細リファレンス
├── examples.md        # オプション: コード例集
└── scripts/           # オプション: 実行可能スクリプト
    ├── helper.py
    └── validate.sh
```

### ファイル分割の基準

- **SKILL.md**: 500行以下。クイックスタートと基本的なワークフロー
- **別ファイルに分割すべき場合**:
  - 詳細なAPIリファレンス → `reference.md`
  - 複数のコード例 → `examples.md`
  - 繰り返し参照する定義 → 専用ファイル

### scripts/ ディレクトリ

`scripts/` 内のファイルはClaudeのコンテキストには読み込まれない。Claudeが実行するためのヘルパースクリプトを配置する。

```markdown
## 検証スクリプト
`scripts/validate.sh` を実行して設定を検証:
\`\`\`bash
bash scripts/validate.sh
\`\`\`
```

## コンテンツガイドライン

**簡潔に**: Claudeは賢い。Claudeが知らない情報のみ追加する。

**SKILL.md本文**: 500行以下に抑える。超える場合は別ファイルに分割。

**参照**: SKILL.mdから1階層のみ。ネストした参照は避ける。

**用語**: 一貫した用語を使用（"API endpoint"と"URL"を混在させない）。

**パス**: 常にスラッシュを使用（`scripts/helper.py`、`scripts\helper.py`ではない）。

## 構造パターン

**ワークフローパターン** - 複数ステップのタスク向け:
```markdown
このチェックリストをコピー:
- [ ] Step 1: Xを実行
- [ ] Step 2: Yを実行
- [ ] Step 3: 検証
```

**段階的開示** - 詳細へのリンク:
```markdown
## クイックスタート
[必須コンテンツ]

**詳細**: [reference.md](reference.md) を参照
```

## 避けるべきこと

- 時間依存の情報（"2025年8月以前は..."）
- 選択肢が多すぎる（"XかYかZを使用..."）
- 曖昧な説明（"ファイルを処理する"）
- Claudeが既に知っていることの過剰説明
