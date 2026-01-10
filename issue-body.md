## 概要
Claude Code v2.1.0でプラグイン仕様に複数の追加・変更がありました。ドキュメントを更新する必要があります。

## 検出された変更内容

### 1. スキル関連の新規フィールド

#### `context: fork` フィールド (スキル/スラッシュコマンド)
- **説明**: スキルやスラッシュコマンドをフォークされたサブエージェントコンテキストで実行可能に
- **CHANGELOG引用**: "Added support for running skills and slash commands in a forked sub-agent context using `context: fork` in skill frontmatter"
- **影響ドキュメント**: `.claude/rules/skill-authoring.md`, `.claude/rules/slash-commands.md`

#### `agent` フィールド (スキル)
- **説明**: スキル実行時に使用するエージェントタイプを指定可能に
- **CHANGELOG引用**: "Added support for `agent` field in skills to specify agent type for execution"
- **影響ドキュメント**: `.claude/rules/skill-authoring.md`

#### `user-invocable: false` フィールド (スキル)
- **説明**: スキルをスラッシュコマンドメニューから非表示にするオプション
- **CHANGELOG引用**: "Improved skills from `/skills/` directories to be visible in the slash command menu by default (opt-out with `user-invocable: false` in frontmatter)"
- **影響ドキュメント**: `.claude/rules/skill-authoring.md`

#### YAML形式リスト対応 (`allowed-tools`)
- **説明**: frontmatterの`allowed-tools`フィールドでYAML形式のリスト記法がサポート
- **CHANGELOG引用**: "Added support for YAML-style lists in frontmatter `allowed-tools` field for cleaner skill declarations"
- **影響ドキュメント**: `.claude/rules/skill-authoring.md`, `.claude/rules/slash-commands.md`, `.claude/rules/agents.md`

### 2. フック関連の拡張

#### `once: true` 設定
- **説明**: フックを一度だけ実行する設定
- **CHANGELOG引用**: "Added support for `once: true` config for hooks"
- **影響ドキュメント**: `.claude/rules/hooks.md`

#### エージェントフロントマターでのフック対応
- **説明**: エージェント定義内でPreToolUse, PostToolUse, Stopフックを定義可能に
- **CHANGELOG引用**: "Added hooks support to agent frontmatter, allowing agents to define PreToolUse, PostToolUse, and Stop hooks scoped to the agent's lifecycle"
- **影響ドキュメント**: `.claude/rules/agents.md`, `.claude/rules/hooks.md`

#### スキル/スラッシュコマンドフロントマターでのフック対応
- **説明**: スキルやスラッシュコマンド定義内でフックを定義可能に
- **CHANGELOG引用**: "Added hooks support for skill and slash command frontmatter"
- **影響ドキュメント**: `.claude/rules/skill-authoring.md`, `.claude/rules/slash-commands.md`, `.claude/rules/hooks.md`

#### プラグインからのprompt/agentフックタイプサポート
- **説明**: 従来はcommandフックのみだったが、prompt/agentフックタイプもプラグインからサポート
- **CHANGELOG引用**: "Added support for prompt and agent hook types from plugins (previously only command hooks were supported)"
- **影響ドキュメント**: `.claude/rules/hooks.md`

### 3. バグ修正

#### `${CLAUDE_PLUGIN_ROOT}` の展開バグ修正
- **説明**: プラグインの`allowed-tools` frontmatter内で`${CLAUDE_PLUGIN_ROOT}`が展開されない問題を修正
- **CHANGELOG引用**: "Fixed `${CLAUDE_PLUGIN_ROOT}` not being substituted in plugin `allowed-tools` frontmatter, which caused tools to incorrectly require approval"
- **影響**: 既存ドキュメントの記述は正しいが、この環境変数が正常に動作するようになったことを明記すべき

## 必要な作業

- [ ] `.claude/rules/skill-authoring.md`: `context`, `agent`, `user-invocable`フィールドの追加
- [ ] `.claude/rules/slash-commands.md`: `context`, `hooks`フィールドの追加
- [ ] `.claude/rules/agents.md`: `hooks`フィールドの追加
- [ ] `.claude/rules/hooks.md`: `once`フィールド、prompt/agentタイプの追記、frontmatter内フック定義の説明追加
- [ ] 全ドキュメント: `allowed-tools`のYAML形式リスト例を追加

## バージョン情報
- **対象バージョン**: Claude Code v2.1.0
- **リリース日**: 2025年1月（推定）

## 関連リンク
- [Claude Code公式CHANGELOG](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md)

