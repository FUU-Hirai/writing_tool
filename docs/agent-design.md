# Agent 設計

## 共通インターフェース

すべての Agent は `BaseAgent` を継承します。

```python
class BaseAgent(ABC):
    name: str

    @abstractmethod
    def build_input(self, context: WorkflowContext) -> dict[str, Any]:
        pass

    async def run(self, context: WorkflowContext) -> AgentResult:
        ...
```

`run` の実装は基底クラスに置いています。サブクラスが担当するのは、入力 JSON の組み立てと構造化出力の型です。LLM 呼び出しは次の形に揃えます。

```python
result = await llm_service.generate(...)
```

Agent は DB を読まず、HTTP リクエストも処理しません。実行記録の保存は Orchestrator が行います。

## コンテキスト

`WorkflowContext` は次を持ちます。

- `article`: テーマ、キーワード、媒体、想定読者、目的、目標文字数、トーン
- `persona`: Persona Agent の出力
- `outline`: Outline Agent の出力
- `draft`: Writer Agent の出力

Agent 同士は直接呼び出しません。Orchestrator が前段の出力をコンテキストへ載せて次へ渡します。

## MVP の実行順

```text
Persona → Outline → Writer → Review
```

疑似コード:

```python
persona = await persona_agent.run(context)
outline = await outline_agent.run(context)   # article + persona
draft = await writer_agent.run(context)       # article + persona + outline
review = await review_agent.run(context)      # article + persona + outline + draft
```

Review の入力に persona と outline を含めるのは、ペルソナとのズレ、目的とのズレ、見出し構成とのズレを点検対象にしているためです。

## Persona Agent

読者像を整理します。本文は書きません。

入力は記事の基本条件です。

出力:

| フィールド | 意味 |
| --- | --- |
| persona | 読者を一文で表したもの |
| problems | 困りごと |
| needs | 記事に求めていること |
| knowledge_level | `beginner` / `intermediate` / `advanced` |
| desired_action | 読後に取ってほしい行動 |

## Outline Agent

Persona の結果と記事条件から見出し構成を作ります。本文は書きません。

出力:

| フィールド | 意味 |
| --- | --- |
| title | 記事タイトル |
| sections[].heading | 見出し |
| sections[].purpose | その節の役割 |
| sections[].points | 節で触れる要点 |

成功時、Orchestrator は `articles.title` をこのタイトルで更新します。

## Writer Agent

構成に沿って Markdown の本文を書きます。事実確認、SEO 監査、推敲判定は対象外です。

入力:

- 記事基本情報
- Persona 結果
- Outline 結果

出力:

| フィールド | 意味 |
| --- | --- |
| title | 原稿タイトル |
| content_markdown | Markdown 本文 |

成功時、この `content_markdown` を `articles.final_content` と `article_versions` に保存します。Review の指摘では本文を更新しません。

## Review Agent

原稿を点検し、指摘だけを返します。

観点:

- 読みにくい文章
- 冗長表現
- 重複
- Persona とのズレ
- 記事目的とのズレ
- 見出し構成とのズレ
- 強すぎる断定

出力:

| フィールド | 意味 |
| --- | --- |
| score | 0〜100 の参考値。業務分岐には使わない |
| issues[].type | 指摘の種類 |
| issues[].target | 該当箇所の短い引用 |
| issues[].reason | 理由 |
| issues[].suggestion | 修正の方向 |
| summary | 全体所感 |

`score` が低くても、パイプラインは失敗にしません。記事ステータスは Agent が例外なく終わったかどうかで決まります。

## Prompt

Prompt 本文は `backend/app/prompts/{agent}/v1.md` に置きます。有効バージョンは `backend/app/prompts/active.json` です。

```text
backend/app/prompts/
├── active.json
├── persona/v1.md
├── outline/v1.md
├── writer/v1.md
└── review/v1.md
```

文言の修正だけなら Markdown を編集します。Agent の Python は変更しません。過去の実行と本文を区別したい場合は `v2.md` を追加し、`active.json` のバージョンだけを切り替えます。実行履歴には、その実行で読んだバージョンを保存します。

バージョン文字列は `v` + 数字だけを許可し、パストラバーサルを避けます。

## 再実行

失敗した地点より前の成功結果を再利用し、指定 Agent から末尾まで実行します。

```text
Persona   success
Outline   success
Writer    failed
Review    pending
```

この場合の再実行は Writer → Review です。Persona と Outline は再呼び出ししません。

先行 Agent に成功結果がない再実行は 400 で拒否します。記事が `processing` の間の再実行は 409 です。

再実行のたびに `agent_runs` は新しい行を追加します。過去行は更新しません。

## 失敗

Agent の例外は Orchestrator が捕捉し、その実行を `failed` として保存してパイプラインを止めます。記事ステータスは `failed` です。Writer が既に成功していれば、保存済みの本文と版は残します。

## Phase 2 以降の追加方法

1. `BaseAgent` を継承したクラスを追加する
2. `prompts/{name}/v1.md` と `active.json` を追加する
3. 出力スキーマを Pydantic で定義する
4. `AGENT_ORDER` と Orchestrator のコンテキスト反映へ登録する
5. 並列が必要になった段階で、順序リストをステージ（並列グループ）へ置き換える

外部データの取得方法は Agent に埋め込みません。Phase 3 の Research Agent は、将来 MCP Client 経由で Google Drive や Notion を参照する想定です。MVP の Agent はリクエストで渡されたコンテキストだけを見ます。
