"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";

import { StatusBadge } from "@/components/StatusBadge";
import { getArticle, getRuns, getVersions, retryAgent } from "@/lib/api";
import { AGENTS, formatDuration, formatTokens, latestByAgent } from "@/lib/agents";
import type { AgentRun, ArticleDetail, ArticleVersion } from "@/lib/types";

export default function ArticleResultPage() {
  const params = useParams<{ id: string }>();
  const articleId = Number(params.id);
  const [article, setArticle] = useState<ArticleDetail | null>(null);
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [versions, setVersions] = useState<ArticleVersion[]>([]);
  const [showMarkdown, setShowMarkdown] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    const [nextArticle, nextRuns, nextVersions] = await Promise.all([
      getArticle(articleId),
      getRuns(articleId),
      getVersions(articleId),
    ]);
    setArticle(nextArticle);
    setRuns(nextRuns);
    setVersions(nextVersions);
  }

  useEffect(() => {
    load().catch((err: Error) => setError(err.message));
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
  const review = latest.get("review");
  const issues = Array.isArray(review?.output_json?.issues) ? review?.output_json?.issues : [];
  const tokenTotal = runs.reduce((sum, run) => sum + (run.input_tokens ?? 0) + (run.output_tokens ?? 0), 0);
  const timeTotal = runs.reduce((sum, run) => sum + (run.execution_time_ms ?? 0), 0);

  return (
    <div className="space-y-8">
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="text-sm text-teal">Result</p>
          <h1 className="font-serif text-4xl">{article?.title ?? "記事結果"}</h1>
        </div>
        <div className="flex items-center gap-3">
          {article && <StatusBadge status={article.status} />}
          <Link href={`/articles/${articleId}`} className="text-sm text-teal">
            実行状況へ
          </Link>
        </div>
      </div>
      {error && <p className="text-sm text-rose-700">{error}</p>}
      <section className="grid gap-4 sm:grid-cols-3">
        <Metric label="使用Token合計" value={formatTokens(tokenTotal)} note="再実行を含む累計" />
        <Metric label="実行時間" value={formatDuration(timeTotal)} note="再実行を含む累計" />
        <Metric label="版" value={String(versions.length)} note={versions[0] ? `最新 v${versions[0].version}` : "未保存"} />
      </section>
      <section className="rounded-2xl border border-line bg-card p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-serif text-2xl">{showMarkdown ? "Markdown" : "完成記事"}</h2>
          <button type="button" className="text-sm text-teal" onClick={() => setShowMarkdown((value) => !value)}>
            {showMarkdown ? "表示を見る" : "Markdown を見る"}
          </button>
        </div>
        {article?.final_content ? (
          showMarkdown ? (
            <pre className="overflow-auto whitespace-pre-wrap text-sm">{article.final_content}</pre>
          ) : (
            <div className="prose-article">
              <ReactMarkdown>{article.final_content}</ReactMarkdown>
            </div>
          )
        ) : (
          <p className="text-stone-600">本文はまだありません。</p>
        )}
      </section>
      <section className="rounded-2xl border border-line bg-card p-6">
        <h2 className="mb-2 font-serif text-2xl">Review結果</h2>
        <p className="mb-4 text-xs text-stone-500">score は参考情報です。完成判定には使いません。</p>
        {review?.output_json ? (
          <div>
            <p className="mb-2 text-sm">参考スコア {String(review.output_json.score)}</p>
            <p className="mb-4">{String(review.output_json.summary ?? "")}</p>
            <ul className="space-y-3">
              {(issues as Array<Record<string, string>>).map((issue, index) => (
                <li key={index} className="rounded-xl bg-paper p-3 text-sm">
                  <p className="font-medium">{issue.type}</p>
                  <p>{issue.target}</p>
                  <p className="text-stone-600">{issue.reason}</p>
                  <p>{issue.suggestion}</p>
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <p className="text-stone-600">Review はまだありません。</p>
        )}
      </section>
      <section className="space-y-3">
        <h2 className="font-serif text-2xl">各Agent結果</h2>
        {AGENTS.map((agent) => {
          const run = latest.get(agent.name);
          return (
            <article key={agent.name} className="rounded-2xl border border-line bg-card p-4">
              <div className="mb-3 flex items-center justify-between">
                <h3 className="font-medium">{agent.label}</h3>
                <div className="flex items-center gap-3">
                  <StatusBadge status={run?.status} />
                  <button
                    type="button"
                    disabled={article?.status === "processing"}
                    onClick={() => onRetry(agent.name)}
                    className="rounded-full border border-ink px-3 py-1 text-sm disabled:opacity-40"
                  >
                    再実行
                  </button>
                </div>
              </div>
              <p className="mb-2 text-xs text-stone-500">
                {formatDuration(run?.execution_time_ms)} / in {formatTokens(run?.input_tokens)} / out {formatTokens(run?.output_tokens)} / {run?.prompt_version ?? "—"} / {run?.model ?? "—"}
              </p>
              {run?.error_message && <p className="mb-2 text-sm text-rose-700">{run.error_message}</p>}
              <pre className="max-h-48 overflow-auto rounded-xl bg-paper p-3 text-xs">
                {run?.output_json ? JSON.stringify(run.output_json, null, 2) : "—"}
              </pre>
            </article>
          );
        })}
      </section>
    </div>
  );
}

function Metric({ label, value, note }: { label: string; value: string; note: string }) {
  return (
    <div className="rounded-2xl border border-line bg-card p-4">
      <p className="text-sm text-stone-500">{label}</p>
      <p className="font-serif text-3xl">{value}</p>
      <p className="text-xs text-stone-500">{note}</p>
    </div>
  );
}
