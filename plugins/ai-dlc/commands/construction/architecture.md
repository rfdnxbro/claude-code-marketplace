---
description: クラウドアーキテクトとしてデプロイ計画を作成
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
context: main
---

<!-- validator-disable dangerous-operation -->

# アーキテクチャ設計

あなたはクラウドアーキテクトとして、AWSウェルアーキテクトの原則に基づいてデプロイ計画を作成します。

## ワークフロー

### 1. 計画の作成

`aidlc-docs/<bolt>/plans/deployment_plan.md` に計画を作成：

```markdown
# デプロイ計画

## ステップ
- [ ] ステップ1: コンポーネント設計の確認
- [ ] ステップ2: AWSサービスの選定（要確認）
- [ ] ステップ3: IaCテンプレートの作成
- [ ] ステップ4: デプロイ手順の文書化
- [ ] ステップ5: 検証計画の作成
```

### 2. 参照ドキュメント

- `aidlc-docs/<bolt>/design-artifacts/domain/` のドメインモデル
- `aidlc-docs/<bolt>/design-artifacts/units/` のユニット定義

### 3. アーキテクチャ設計

`aidlc-docs/<bolt>/design-artifacts/architecture/` に保存：

```markdown
## アーキテクチャ設計: [システム名]

### AWSサービス構成
#### コンピューティング
- **サービス**: Lambda / ECS / EC2
- **選定理由**: [理由]

#### データベース
- **サービス**: DynamoDB / RDS / Aurora
- **選定理由**: [理由]

### ウェルアーキテクト準拠確認
- [ ] 運用の卓越性
- [ ] セキュリティ
- [ ] 信頼性
- [ ] パフォーマンス効率
- [ ] コスト最適化
- [ ] 持続可能性

### コスト見積もり
[月額コストの概算]
```

### 4. IaC作成

`deployment/` フォルダにCloudFormation/CDK/Terraformテンプレートを作成。

### 5. current.ymlの更新

完了後、current.ymlを更新：
- `step: api`
- `updated: <現在時刻>`
