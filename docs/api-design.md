# API 設計

ベース URL はバックエンドの `/api` です。ブラウザからは Next.js の `/api` を呼び、サーバーがバックエンドへ転送します。

リクエストとレスポンスは JSON です。日時は ISO 8601 です。

## エンドポイント

| メソッド | パス | 用途 |
| --- | --- | --- |
| POST | `/api/articles` | 記事を下書き作成 |
| GET | `/api/articles` | 記事一覧 |
| GET | `/api/articles/{id}` | 記事詳細 |
| POST | `/api/articles/{id}/generate` | 先頭から生成 |
| GET | `/api/articles/{id}/runs` | Agent 実行履歴 |
| POST | `/api/articles/{id}/agents/{agent_name}/retry` | 指定 Agent から再実行 |
| GET | `/api/articles/{id}/versions` | 本文の版一覧 |
| GET | `/health` | 死活確認 |

`agent_name` は `persona`、`outline`、`writer`、`review` です。

## POST /api/articles

リクエスト:

```json
{
  "theme": "AI導入で最初にやるべきこと",
  "keyword": "AI 導入",
  "media": "note",
  "target_audience": "AI初心者の企業担当者",
  "purpose": "AIコンサル問い合わせ",
  "target_length": 4000,
  "tone": "実務的で初心者にもわかりやすい"
}
```

| フィールド | ルール |
| --- | --- |
| theme | 1〜2000 文字 |
| keyword | 1〜255 文字 |
| media | 1〜100 文字 |
| target_audience | 1〜2000 文字 |
| purpose | 1〜2000 文字 |
| target_length | 300〜20000 |
| tone | 1〜1000 文字 |

レスポンス `201`:

```json
{
  "id": 1,
  "status": "draft"
}
```

作成時のタイトルはテーマです。Outline 成功後に生成タイトルへ更新します。

## GET /api/articles

作成日時の降順です。一覧には本文を含めません。

```json
[
  {
    "id": 1,
    "title": "AI導入で最初にやるべきこと",
    "theme": "AI導入で最初にやるべきこと",
    "status": "completed",
    "created_at": "2026-09-25T09:00:00Z"
  }
]
```

## GET /api/articles/{id}

一覧項目に加え、キーワード、媒体、想定読者、目的、目標文字数、トーン、`final_content`、`updated_at` を返します。`final_content` は未生成のとき `null` です。

## POST /api/articles/{id}/generate

全 Agent を Persona から実行します。受け付け時点で状態を `processing` にしてから処理を開始します。

レスポンス `200`:

```json
{
  "id": 1,
  "status": "processing"
}
```

完了や失敗は、このレスポンスでは待ちません。`GET /api/articles/{id}` と `GET /api/articles/{id}/runs` で確認します。

## GET /api/articles/{id}/runs

id の昇順で全履歴を返します。

```json
[
  {
    "id": 10,
    "article_id": 1,
    "agent_name": "persona",
    "status": "success",
    "input_json": {},
    "output_json": {},
    "model": "gpt-4o-mini",
    "prompt_version": "v1",
    "input_tokens": 120,
    "output_tokens": 80,
    "execution_time_ms": 1500,
    "error_message": null,
    "started_at": "2026-09-25T09:00:01Z",
    "completed_at": "2026-09-25T09:00:02Z",
    "created_at": "2026-09-25T09:00:01Z"
  }
]
```

## POST /api/articles/{id}/agents/{agent_name}/retry

`agent_name` と、それより後ろの Agent だけを実行します。前段は最新の `success` 行の `output_json` を使います。

レスポンスは generate と同じく `id` と `status: processing` です。

先行 Agent の成功結果がない場合は 400 です。

```json
{
  "detail": "outline を再実行するには、先に persona の成功結果が必要です"
}
```

## GET /api/articles/{id}/versions

版番号の降順です。

```json
[
  {
    "id": 3,
    "article_id": 1,
    "version": 2,
    "content": "# タイトル\n\n本文",
    "created_at": "2026-09-25T09:10:00Z"
  }
]
```

Writer が成功するたびに版が増えます。Review だけでは増えません。

## エラー

| コード | 条件 |
| --- | --- |
| 400 | 未知の Agent、再実行に必要な成功結果がない |
| 404 | 記事が存在しない |
| 409 | その記事がすでに `processing` |
| 422 | リクエストボディがスキーマに合わない |
| 500 | 未処理のサーバーエラー |

Agent 実行中の OpenAI やパースの失敗は HTTP エラーにはしません。実行行を `failed` にし、記事を `failed` にします。クライアントは runs の `error_message` を表示します。

`error_message` の代表値:

| メッセージ | 状況 |
| --- | --- |
| OpenAI API timeout | タイムアウト |
| OpenAI API rate limit | レート制限 |
| Structured output parse error | 構造化出力のパース失敗 |
| OpenAI API error | その他の API エラー |
| OpenAI credential is not configured | キー未設定 |
| Agent error | メッセージに秘匿情報が含まれうる内部エラー |
| DB error | データベースエラー |

## curl 例

```bash
curl -s -X POST http://localhost:8000/api/articles \
  -H 'Content-Type: application/json' \
  -d '{
    "theme": "AI導入で最初にやるべきこと",
    "keyword": "AI 導入",
    "media": "note",
    "target_audience": "AI初心者の企業担当者",
    "purpose": "AIコンサル問い合わせ",
    "target_length": 4000,
    "tone": "実務的で初心者にもわかりやすい"
  }'
```
