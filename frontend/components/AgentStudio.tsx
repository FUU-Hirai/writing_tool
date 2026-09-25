"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { StatusBadge } from "@/components/StatusBadge";
import { getArticle, getRuns, retryAgent } from "@/lib/api";
import { AGENTS, formatDuration, formatTokens, latestByAgent } from "@/lib/agents";
import type { AgentRun, ArticleDetail } from "@/lib/types";

export function AgentStudio({ articleId }: { articleId: number }) {
  const [article, setArticle] = useState<ArticleDetail | null>(null);
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [selected, setSelected] = useState("persona");
  const [error, setError] = useState<string | null>(null);

  async function load() {
    const [nextArticle, nextRuns] = await Promise.all([getArticle(articleId), getRuns(articleId)]);
    setArticle(nextArticle);
    setRuns(nextRuns);
    return nextArticle;
  }

  useEffect(() => {
    let timer = 0;
    let stop = false;
    async function tick() {
      try {
        const current = await load();
        if (!stop && current.status === "processing") {
          timer = window.setTimeout(tick, 2000);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "読み込みに失敗しました");
      }
    }
    tick();
    return () => {
      stop = true;
      window.clearTimeout(timer);
    };
  }, [articleId]);

  async function onRetry(agentName: string) {
    setError(null);
    try {
      await retryAgent(articleId, agentName);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "再実行に失敗しました");
    }
  }

  const latest = latestByAgent(runs);
  const selectedRun = latest.get(selected);
  const historyCount = runs.filter((run) => run.agent_name === selected).length;

  return (
    <div>
      <div className="mb-8 flex items-end justify-between gap-4">
        <div>
          <p className="text-sm text-teal">Agent run</p>
          <h1 className="font-serif text-4xl">{article?.title ?? "Agent実行状況"}</h1>
        </div>
        <div className="flex items-center gap-3">
          {article && <StatusBadge status={article.status} />}
          <Link href={`/articles/${articleId}/result`} className="text-sm text-teal">
            記事結果へ
          </Link>
        </div>
      </div>
      {error && <p className="mb-4 text-sm text-rose-700">{error}</p>}
      <ol className="space-y-3">
        {AGENTS.map((agent) => {
          const run = latest.get(agent.name);
          const active = selected === agent.name;
          return (
            <li key={agent.name}>
              <button
                type="button"
                onClick={() => setSelected(agent.name)}
                className={`flex w-full items-center justify-between rounded-2xl border px-5 py-4 text-left ${active ? "border-teal bg-card" : "border-line bg-card/60"}`}
              >
                <span>
                  <span className="block font-medium">{agent.label}</span>
                  <span className="text-sm text-stone-500">{agent.description}</span>
                </span>
                <StatusBadge status={run?.status} />
              </button>
            </li>
          );
        })}
      </ol>
      <section className="mt-6 rounded-2xl border border-line bg-card p-5">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-serif text-2xl">{selected}</h2>
          <button
            type="button"
            disabled={article?.status === "processing"}
            onClick={() => onRetry(selected)}
            className="rounded-full border border-ink px-3 py-1 text-sm disabled:opacity-40"
          >
            再実行
          </button>
        </div>
        <dl className="mb-4 grid gap-3 text-sm sm:grid-cols-4">
          <div>
            <dt className="text-stone-500">status</dt>
            <dd>{selectedRun?.status ?? "pending"}</dd>
          </div>
          <div>
            <dt className="text-stone-500">execution time</dt>
            <dd>{formatDuration(selectedRun?.execution_time_ms)}</dd>
          </div>
          <div>
            <dt className="text-stone-500">token usage</dt>
            <dd>
              in {formatTokens(selectedRun?.input_tokens)} / out {formatTokens(selectedRun?.output_tokens)}
            </dd>
          </div>
          <div>
            <dt className="text-stone-500">実行回数</dt>
            <dd>{historyCount}</dd>
          </div>
        </dl>
        {selectedRun?.error_message && <p className="mb-4 rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-800">{selectedRun.error_message}</p>}
        <div className="grid gap-4 lg:grid-cols-2">
          <JsonBlock title="input" value={selectedRun?.input_json} />
          <JsonBlock title="output" value={selectedRun?.output_json} />
        </div>
      </section>
    </div>
  );
}

function JsonBlock({ title, value }: { title: string; value: unknown }) {
  return (
    <div>
      <h3 className="mb-2 text-sm text-stone-500">{title}</h3>
      <pre className="max-h-80 overflow-auto rounded-xl bg-ink p-3 text-xs text-paper">
        {value ? JSON.stringify(value, null, 2) : "—"}
      </pre>
    </div>
  );
}
