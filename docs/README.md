# Multi-Agent Article Studio ドキュメント

このディレクトリは、アプリの要件・設計・開発手順をコードから独立して残す場所です。仕様の変更は、対応するドキュメントも同時に更新します。

| ドキュメント | 役割 |
| --- | --- |
| [requirements.md](./requirements.md) | 要件定義。目的、利用者、MVP の範囲、将来機能 |
| [architecture.md](./architecture.md) | システム全体構成とレイヤ責務 |
| [agent-design.md](./agent-design.md) | Agent ごとの責務、入出力、連携、再実行 |
| [database-design.md](./database-design.md) | テーブル定義と保存ルール |
| [api-design.md](./api-design.md) | REST API の仕様 |
| [development-guide.md](./development-guide.md) | ローカル開発、起動、テスト、マイグレーション |
| [decisions/](./decisions/) | 技術選定と設計判断の記録（ADR） |

## 読む順番

1. [requirements.md](./requirements.md) で何を作るかを確認する
2. [architecture.md](./architecture.md) で処理の流れを確認する
3. [agent-design.md](./agent-design.md) と [api-design.md](./api-design.md)、[database-design.md](./database-design.md) で詳細を確認する
4. 実装や起動は [development-guide.md](./development-guide.md) に従う

## 現在の実装範囲

Phase 1 までを実装しています。Pipeline は次の 4 Agent です。

```text
Persona → Outline → Writer → Review
```

Research / SEO / Fact Check / Editor / Finalizer、および外部連携は Phase 2 以降です。追加時は Agent をパイプラインへ登録し、このディレクトリの該当文書を更新します。
