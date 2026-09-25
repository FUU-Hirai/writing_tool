# 要件定義

## 目的

記事制作工程を複数の AI Agent へ分割し、それぞれが役割を持って協調することで記事を生成する。単一の LLM 呼び出しに構成・執筆・点検をまとめない。

## 想定ユーザー

- オウンドメディア担当者
- SEO 担当者
- note / ブログ運営者
- コンテンツマーケター

認証は MVP の対象外です。ローカル、または閉じたネットワークでのプロトタイプ利用を想定します。

## MVP 入力項目

| 項目 | 内容 |
| --- | --- |
| 記事テーマ | 何について書くか |
| メインキーワード | 記事の中心になる語句 |
| 媒体 | note、ブログ、オウンドメディアなど |
| 想定読者 | 誰に読ませるか |
| 記事目的 | 読後に起きてほしいこと |
| 目標文字数 | 本文の目安 |
| トーン | 文体の指示 |

## MVP 機能

- 記事作成
- Agent 実行
- Agent 進捗表示
- Agent ごとの結果確認
- 完成記事表示
- 記事保存
- 実行履歴保存
- Agent 単位の再実行
- 過去記事一覧

完成記事は Writer Agent の Markdown です。Review Agent は指摘を返すだけで、本文を書き換えません。`score` は画面上の参考値であり、合格・不合格や再実行の判定には使いません。

## 画面

- 記事一覧
- 新規記事作成
- Agent 実行状況
- 記事結果

## 将来機能

Phase 2:

- Research Agent
- SEO Agent
- Fact Check Agent
- Editor Agent
- Finalizer Agent

Phase 3:

- MCP 連携
- Google Drive / Notion 連携
- WordPress 連携
- Web 検索

## MVP で導入しないもの

- Kubernetes
- Kafka
- 複雑な RAG
- Vector DB
- 過剰なマイクロサービス
- 常駐のジョブキュー

ジョブの入口は `run_article_workflow` にまとめてあり、将来この関数をキューワーカーから呼べるようにします。MVP の実行本体は API プロセス内のバックグラウンドタスクです。

## エラーとして扱うもの

- OpenAI API のタイムアウト
- レート制限
- 不正なレスポンス
- Structured Output のパース失敗
- DB エラー
- Agent 内部エラー

Agent が失敗した場合も、失敗ステータスとエラーメッセージを `agent_runs` に残します。失敗した Agent より前の成功結果は保持し、その Agent から先だけ再実行できます。

## 受入条件（Phase 1）

- Docker Compose で frontend / backend / postgres が起動する
- 記事を登録し、4 Agent を順に実行できる
- 進捗、入出力、トークン、実行時間、完成記事を画面で確認できる
- 失敗が DB に残り、該当 Agent から再実行できる
- Prompt が Python コードから分離されている
- Agent、Orchestrator、API のテストがある
- この `docs/` とルート README から仕様を辿れる
