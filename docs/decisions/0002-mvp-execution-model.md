# ADR 0002: MVP の実行モデル

## Status

Accepted

## Context

Phase 1 では 4 Agent を確実に追跡・再実行できる必要がある。同時に、プロトタイプへキューや並列実行基盤を先に入れない、という制約がある。Review の点数を業務判定に使うと、記事完成条件が不透明になる。

## Decision

1. 生成は FastAPI のバックグラウンドタスクで行い、画面は記事と `agent_runs` をポーリングする。キューは導入しない。ワーカーへ移すときの入口は `run_article_workflow` に限定する。
2. `processing` への更新は、タスクを起動する前にコミットする。リクエスト終了時のトランザクションが、タスクの完了状態を上書きしないようにする。
3. MVP の完成記事は Writer の Markdown とする。Review は指摘のみ返し、本文もステータスも `score` では変えない。本文の書き換えは Phase 2 の Finalizer の責務にする。
4. 再実行は指定 Agent から末尾までとする。前段は最新の成功出力を再利用する。
5. Prompt 本文は Markdown に置き、有効バージョンは `prompts/active.json` で選ぶ。
6. 実行時のデータベースは PostgreSQL、自動テストは SQLite とする。モデル定義は共通にする。
7. ブラウザは Next.js の同一オリジン `/api` を呼び、Next.js がバックエンドへ転送する。

## Reasons

- 進捗表示と失敗箇所の特定に、別プロセスのキューは不要だった
- コミット順を決めておかないと、完了した記事が `processing` に戻る
- Review を自動修正にすると、Writer の責務と実行履歴の意味が混ざる
- Provider と DB を差し替えられると、OpenAI なしで Agent と API をテストできる

## Consequences

- API プロセスが生成中に止まると、その実行は `running` のまま残ることがある。MVP では手動の再実行で回復する
- 同時に二つの生成要求が走らないよう、`processing` 中は 409 を返す。分散ロックは持たない
- 並列 Agent が必要になったときは、Orchestrator の直列リストをステージ定義へ置き換える。Agent 側の `run` は変更しない
