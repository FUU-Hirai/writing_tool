# ADR 0001: 初期アーキテクチャ

## Status

Accepted

## Context

マルチエージェントによる記事生成アプリを構築する。

## Decision

FastAPI + Next.js + PostgreSQL を採用する。

Agent / Orchestrator / LLMService / Repository を分離する。

## Reasons

- Agent 単位のテストが可能
- Model Provider の変更が容易
- Agent 追加が容易
- 障害調査が容易

## Consequences

単純な LLM アプリよりファイル数は増えるが、保守性・拡張性を優先する。
