# Multi-Agent Article Studio

## Overview

テーマ、媒体、読者、目的を入力すると、役割の違う AI Agent が順に記事を作る Web アプリケーションです。Phase 1 では Persona、Outline、Writer、Review の 4 Agent を直列に実行します。

詳細な要件は [docs/requirements.md](docs/requirements.md) を参照してください。

## Architecture

```text
Next.js → REST API → FastAPI → ArticleService → ArticleWorkflow
  → Agents → LLMService → OpenAI API
```

保存は Repository から PostgreSQL へ行います。全体構成は [docs/architecture.md](docs/architecture.md)、判断の記録は [docs/decisions/](docs/decisions/) にあります。

## Multi-Agent Workflow

```text
Persona → Outline → Writer → Review
```

Orchestrator が順番だけを管理し、各 Agent が専門処理を担当します。Review のスコアは画面上の参考値で、完成判定には使いません。失敗した Agent から先だけ再実行できます。

Agent の入出力は [docs/agent-design.md](docs/agent-design.md) を参照してください。

## Tech Stack

- Frontend: Next.js, TypeScript, React, Tailwind CSS
- Backend: Python, FastAPI, Pydantic, SQLAlchemy
- Database: PostgreSQL
- AI: OpenAI API（Agent は LLMService 経由でのみ呼び出す）
- Development: Docker Compose

## Getting Started

```bash
cp .env.example .env
# .env の OPENAI_API_KEY を設定する
docker compose up --build
```

- 画面: http://localhost:3000
- API: http://localhost:8000/docs

起動手順の詳細は [docs/development-guide.md](docs/development-guide.md) を参照してください。

## Environment Variables

`.env.example` が雛形です。`.env` は Git 管理しません。

| 変数 | 用途 |
| --- | --- |
| OPENAI_API_KEY | OpenAI API キー |
| OPENAI_MODEL | 使用モデル |
| DATABASE_URL | ホストからバックエンドを起動するときの接続文字列 |
| INTERNAL_API_URL | Next.js から見た API。Compose では `http://backend:8000` |

## Database Migration

Compose 起動時に `alembic upgrade head` が実行されます。テーブル定義は [docs/database-design.md](docs/database-design.md) を参照してください。

```bash
cd backend
alembic upgrade head
```

## Running Tests

OpenAI は呼び出しません。

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

## Directory Structure

```text
├── README.md
├── docker-compose.yml
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
    └── tests/
```

## Documentation

| 文書 | 内容 |
| --- | --- |
| [docs/README.md](docs/README.md) | ドキュメント一覧 |
| [docs/requirements.md](docs/requirements.md) | 要件定義 |
| [docs/architecture.md](docs/architecture.md) | システム構成 |
| [docs/agent-design.md](docs/agent-design.md) | Agent 設計 |
| [docs/database-design.md](docs/database-design.md) | DB 設計 |
| [docs/api-design.md](docs/api-design.md) | REST API |
| [docs/development-guide.md](docs/development-guide.md) | 開発・起動手順 |
| [docs/decisions/](docs/decisions/) | ADR |

## Future Roadmap

- Phase 2: Research、SEO、Fact Check、Editor、Finalizer
- Phase 3: MCP、Google Drive、Notion、WordPress、Web 検索

Phase 2 以降は Phase 1 が動作してから追加します。
# writing_tool
