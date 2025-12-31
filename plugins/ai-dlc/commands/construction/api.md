---
description: ソフトウェアエンジニアとしてREST APIを作成
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

<!-- validator-disable dangerous-operation -->

# REST API作成

あなたはソフトウェアエンジニアとして、サービス層に対するREST APIを作成します。

## ワークフロー

### 1. 計画の作成

`aidlc-docs/<bolt>/plans/api_plan.md` に計画を作成：

```markdown
# API作成計画

## ステップ
- [ ] ステップ1: サービス層の確認
- [ ] ステップ2: APIエンドポイントの設計（要確認）
- [ ] ステップ3: リクエスト/レスポンス形式の定義
- [ ] ステップ4: APIコードの生成
- [ ] ステップ5: APIテストの作成と実行
```

### 2. サービス参照

生成済みのサービスコードを参照。

### 3. API設計

```markdown
## API設計: [サービス名]

### エンドポイント一覧
| Method | Path | 説明 |
|--------|------|------|
| GET | /api/v1/resources | リソース一覧取得 |
| POST | /api/v1/resources | リソース作成 |
| GET | /api/v1/resources/{id} | リソース取得 |
| PUT | /api/v1/resources/{id} | リソース更新 |
| DELETE | /api/v1/resources/{id} | リソース削除 |

### リクエスト/レスポンス形式
[各エンドポイントの詳細]
```

### 4. APIコード生成

選択されたフレームワーク（Flask, FastAPI等）でAPIを実装。

### 5. テスト

APIエンドポイントのテストを作成・実行。

### 6. current.ymlの更新

完了後、ボルトの完了を示すように更新。
