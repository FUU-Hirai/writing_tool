# データベース設計

PostgreSQL を正とします。テストは同じ SQLAlchemy モデルを SQLite に対して実行します。JSON は JSONB ではなく汎用の JSON 型で定義し、テストと本番でモデルを分岐させません。

マイグレーションは Alembic です。初期リビジョンは `0001_initial` です。

## ER

```text
articles 1 ─── * agent_runs
articles 1 ─── * article_versions
```

記事を削除した場合、実行履歴と版は CASCADE で削除します。MVP の API に削除エンドポイントはありません。

## articles

記事の入力条件、進行状態、最新の本文を保持します。

| カラム | 型 | 制約 | 説明 |
| --- | --- | --- | --- |
| id | integer | PK | |
| title | varchar(500) | NOT NULL | 作成時はテーマ。Outline 成功後に生成タイトル |
| theme | text | NOT NULL | 記事テーマ |
| keyword | varchar(255) | NOT NULL | メインキーワード |
| media | varchar(100) | NOT NULL | 媒体 |
| target_audience | text | NOT NULL | 想定読者 |
| purpose | text | NOT NULL | 記事目的 |
| target_length | integer | NOT NULL | 目標文字数 |
| tone | text | NOT NULL | トーン |
| status | varchar(32) | NOT NULL | 下記 |
| final_content | text | NULL | 最新の Writer 原稿 |
| created_at | timestamptz | NOT NULL | |
| updated_at | timestamptz | NOT NULL | |

`status`:

| 値 | 意味 |
| --- | --- |
| draft | 作成直後。未実行 |
| processing | Agent 実行中 |
| completed | 4 Agent が成功 |
| failed | いずれかの Agent が失敗 |

`final_content` は Writer が成功した時点で更新します。その後 Review が失敗しても本文は残し、状態だけ `failed` にします。再生成で成功した場合は最新本文へ更新し、直前の本文は `article_versions` に残っています。

## agent_runs

Agent 実行の監査ログです。1 回の実行につき 1 行で、再実行でも上書きしません。

| カラム | 型 | 制約 | 説明 |
| --- | --- | --- | --- |
| id | integer | PK | |
| article_id | integer | FK, index | articles.id |
| agent_name | varchar(50) | NOT NULL | persona / outline / writer / review |
| status | varchar(32) | NOT NULL | 下記 |
| input_json | json | NULL | Agent へ渡した入力 |
| output_json | json | NULL | 構造化出力 |
| model | varchar(100) | NULL | 使用モデル |
| prompt_version | varchar(20) | NULL | 例: v1 |
| input_tokens | integer | NULL | |
| output_tokens | integer | NULL | |
| execution_time_ms | integer | NULL | |
| error_message | text | NULL | 失敗時の公開用メッセージ |
| started_at | timestamptz | NULL | |
| completed_at | timestamptz | NULL | |
| created_at | timestamptz | NOT NULL | |

`status`:

| 値 | 意味 |
| --- | --- |
| pending | 予約。MVP では実行開始時に running で作るため、通常の行では使わない |
| running | 実行中 |
| success | 成功 |
| failed | 失敗 |

このテーブルで、どの Agent が、何を入力され、何を出力し、どのモデルと Prompt バージョンを使い、何トークンを使い、何ミリ秒かかり、成功したか失敗したかを追えます。

失敗行の例:

```json
{
  "status": "failed",
  "error_message": "OpenAI API timeout"
}
```

画面のパイプラインは、Agent ごとの最新行（最大 id）を現在状態として表示します。

## article_versions

Writer が成功するたびに本文の版を追加します。上書きはしません。

| カラム | 型 | 制約 | 説明 |
| --- | --- | --- | --- |
| id | integer | PK | |
| article_id | integer | FK, index | articles.id |
| version | integer | NOT NULL | 記事内で 1 から増加 |
| content | text | NOT NULL | Markdown |
| created_at | timestamptz | NOT NULL | |

`(article_id, version)` は一意です。

## インデックス

- `agent_runs.article_id`
- `article_versions.article_id`
- `ix_agent_runs_article_agent` (`article_id`, `agent_name`)

最新の成功結果を再実行時に引くための索引です。
