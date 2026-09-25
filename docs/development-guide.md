# 開発ガイド

## 実装の進め方

1. リポジトリは空だったため、新規構成で Phase 1 を実装した
2. 設計は `docs/` に残し、Phase 2 の Agent はパイプライン未登録のまま拡張点だけ用意した
3. 最初の動作確認対象は、記事 CRUD、4 Agent の直列実行、履歴、再実行、画面表示

Phase 2 以降は、Phase 1 のテストと起動が崩れていないことを確認してから追加します。

## 前提

- Docker Compose v2
- ローカルでテストだけ実行する場合は Python 3.12 と Node.js 22

## 環境変数

リポジトリ直下に `.env` を作ります。`.env` は Git 管理外です。

```bash
cp .env.example .env
```

| 変数 | 用途 |
| --- | --- |
| OPENAI_API_KEY | OpenAI の API キー。未設定でも API は起動し、生成時に失敗として記録する |
| OPENAI_MODEL | 使用モデル。既定は `gpt-4o-mini` |
| OPENAI_TIMEOUT_SECONDS | 1 呼び出しのタイムアウト秒。既定は 120 |
| OPENAI_MAX_TOKENS | 最大出力トークン。既定は 12000 |
| DATABASE_URL | ローカルでバックエンドを直接起動するときの接続文字列 |
| POSTGRES_USER / POSTGRES_PASSWORD / POSTGRES_DB | Compose の PostgreSQL |
| INTERNAL_API_URL | Next.js から見たバックエンド。Compose では `http://backend:8000` |

キーや接続文字列をコード、ログ、Prompt に書きません。

## Docker Compose で起動する

```bash
docker compose up --build
```

| サービス | URL |
| --- | --- |
| 画面 | http://localhost:3000 |
| API | http://localhost:8000 |
| API ドキュメント | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |

バックエンド起動時に PostgreSQL の準備を待ち、`alembic upgrade head` を実行してから Uvicorn を起動します。

停止:

```bash
docker compose down
```

データを消してやり直す場合:

```bash
docker compose down -v
```

## データベースマイグレーション

Compose 内では起動時に適用されます。ホストからバックエンドディレクトリで適用する場合:

```bash
cd backend
alembic upgrade head
```

新しいリビジョン:

```bash
cd backend
alembic revision -m "describe the change"
```

モデルと `backend/alembic/versions/` の両方を更新し、[database-design.md](./database-design.md) に反映します。

## テスト

テストは OpenAI を呼びません。LLM Provider を差し替えます。DB はプロセス内の SQLite です。

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

| テスト | 確認すること |
| --- | --- |
| `tests/agents/` | 入力の組み立て、Prompt ファイルの使用、例外の伝播 |
| `tests/orchestrators/test_article_workflow.py` | 実行順、低スコアでも完了すること、失敗の保存、途中再実行、秘匿情報を保存しないこと |
| `tests/api/test_articles.py` | CRUD、生成、履歴、版、再実行、409 / 404 / 400 |

## ローカルでプロセスを分けて起動する

PostgreSQL だけ Compose で起動する例:

```bash
docker compose up postgres
```

バックエンド:

```bash
cd backend
source .venv/bin/activate
export DATABASE_URL=postgresql+asyncpg://studio:studio@localhost:5432/article_studio
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

フロントエンド:

```bash
cd frontend
npm install
npm run dev
```

`INTERNAL_API_URL` 未設定時、Next.js は `http://localhost:8000` へ転送します。

## ディレクトリ

```text
writing_tool/
├── README.md
├── docker-compose.yml
├── .env.example
├── docs/
├── frontend/
└── backend/
    ├── app/
    │   ├── api/
    │   ├── agents/
    │   ├── orchestrators/
    │   ├── services/
    │   ├── repositories/
    │   ├── models/
    │   ├── schemas/
    │   └── prompts/
    ├── alembic/
    └── tests/
```

## トラブルシュート

- 生成がすぐに失敗する: `.env` の `OPENAI_API_KEY` を確認する。失敗理由は画面の Agent 詳細と `agent_runs.error_message` に出ます
- ポート 3000 / 8000 / 5432 が使用中: 既存プロセスを止めるか、Compose のポートを変更する
- 画面は開くが API が失敗する: `docker compose ps` で backend が healthy になるまで待つ。backend ログにマイグレーションエラーが出ていないか確認する
