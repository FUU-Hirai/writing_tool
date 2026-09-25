# アーキテクチャ

## 全体像

```text
Next.js
   ↓  同一オリジン /api （Next.js がバックエンドへプロキシ）
REST API
   ↓
FastAPI
   ↓
ArticleService
   ↓
ArticleWorkflow / Orchestrator
   ↓
Agents
   ↓
LLMService
   ↓
OpenAI API
```

データ保存:

```text
FastAPI
   ↓
Repository
   ↓
PostgreSQL
```

ブラウザは Next.js の Route Handler 経由で API を呼びます。サーバー側の転送先は `INTERNAL_API_URL`（Compose 内では `http://backend:8000`）です。ブラウザにバックエンドのホストを埋め込まないため、コンテナ間通信とローカル開発を同じフロントエンドコードで扱えます。

## リクエストの流れ

1. 画面が `POST /api/articles` で下書きを作る
2. `POST /api/articles/{id}/generate` が状態を `processing` にしてコミットする
3. コミット後にバックグラウンドタスクが `run_article_workflow` を実行する
4. 画面は記事と `agent_runs` をポーリングする
5. Writer 成功時に本文と版を保存する
6. 4 Agent が成功すると記事状態を `completed` にする

状態を先にコミットするのは、タスク開始後にリクエスト側のトランザクションが `processing` を上書きしないためです。詳細は [ADR 0002](./decisions/0002-mvp-execution-model.md) にあります。

## レイヤ責務

### API Layer

`backend/app/api/`

HTTP の入出力、ステータスコード、バックグラウンドタスクの登録だけを担当します。分岐を伴う業務ルールは書きません。

### Service Layer

`backend/app/services/article_service.py`

記事作成、取得、生成開始、再実行開始のユースケースを担当します。再実行に必要な先行 Agent の成功有無もここで確認します。

### Orchestrator

`backend/app/orchestrators/article_workflow.py`

Agent の実行順序、実行記録、失敗時の停止、本文と版の保存を担当します。記事本文そのものは生成しません。各 Agent のプロンプトや編集判断を持ちません。

将来キューへ移すときの入口は `run_article_workflow(article_id, start_from)` です。

### Agent

`backend/app/agents/`

専門処理だけを担当します。DB、HTTP リクエスト、他 Agent の具象クラスには依存しません。入力は `WorkflowContext`、出力は Pydantic モデルです。

### LLMService

`backend/app/services/llm_service.py`

Prompt ファイルの読み込み、Provider 呼び出し、レスポンスとトークン使用量の返却を担当します。OpenAI SDK を import するのは `openai_provider.py` だけです。

### Repository

`backend/app/repositories/`

SQLAlchemy による永続化だけを担当します。業務上の実行順序は知りません。

## MVP パイプライン

```text
Persona
  ↓
Outline
  ↓
Writer
  ↓
Review
```

Phase 2 で想定する形は次のとおりです。MVP では並列ステージを実装しません。

```text
                 ┌ Persona
Article ─────────┼ Research
                 └ SEO
                     ↓
                   Outline
                     ↓
                   Writer
                     ↓
               ┌ FactCheck
               └ Editor
                     ↓
                  Finalizer
```

Agent 実装はすべて `async def run` です。並列化は Orchestrator のステージ定義を変える拡張点として残します。

## プロセス構成

Docker Compose のサービスは次の 3 つです。

| サービス | 役割 |
| --- | --- |
| frontend | Next.js |
| backend | FastAPI |
| postgres | PostgreSQL 16 |

## ログ

Orchestrator は Agent 完了ごとに次を INFO ログへ出します。

- `article_id`
- `agent_name`
- `status`
- `execution_time_ms`
- `input_tokens`
- `output_tokens`
- `error`

API キー、Prompt 本文、Authorization ヘッダーはログに出しません。例外メッセージに `sk-` が含まれる場合は、DB とログの双方で `Agent error` に置き換えます。
