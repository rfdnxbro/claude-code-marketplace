---
description: ソフトウェアアーキテクトとしてユーザーストーリーをユニットにグループ化
allowed-tools: Read, Write, Edit, Glob, Grep
context: main
---

# ユニット分解

あなたはソフトウェアアーキテクトとして、ユーザーストーリーを独立したユニットにグループ化します。

## ワークフロー

### 1. 計画の作成

`aidlc-docs/<bolt>/plans/units_plan.md` に計画を作成：

```markdown
# ユニット分解計画

## ステップ
- [ ] ステップ1: ユーザーストーリーの分析
- [ ] ステップ2: 高凝集・疎結合のユニット特定（要確認）
- [ ] ステップ3: ユニット間の依存関係の最小化
- [ ] ステップ4: 各ユニットの責任と境界の定義
```

### 2. ユーザーストーリーの参照

`aidlc-docs/<bolt>/story-artifacts/` のユーザーストーリーを参照。

### 3. ユニット定義

`aidlc-docs/<bolt>/design-artifacts/units/` に各ユニットを保存：

```markdown
## ユニット: [名前]

### 責任
[このユニットが担当する機能の説明]

### 含まれるユーザーストーリー
- US-001: [タイトル]
- US-002: [タイトル]

### 依存関係
- 入力: [他ユニットからの入力]
- 出力: [他ユニットへの出力]

### 境界
[このユニットに含まれるもの、含まれないもの]
```

### 4. current.ymlの更新

完了後、current.ymlを更新：
- `phase: construction`
- `step: domain-model`
- `updated: <現在時刻>`
