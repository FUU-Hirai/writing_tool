"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { StatusBadge } from "@/components/StatusBadge";
import { listArticles } from "@/lib/api";
import { formatDate } from "@/lib/agents";
import type { ArticleSummary } from "@/lib/types";

export default function ArticleListPage() {
  const [articles, setArticles] = useState<ArticleSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listArticles()
      .then(setArticles)
      .catch((err: Error) => setError(err.message));
  }, []);

  return (
    <div>
      <div className="mb-8 flex items-end justify-between">
        <div>
          <p className="text-sm text-teal">Article list</p>
          <h1 className="font-serif text-4xl">記事一覧</h1>
        </div>
        <Link href="/articles/new" className="rounded-full bg-ink px-4 py-2 text-sm text-paper">
          新規記事作成
        </Link>
      </div>
      {error && <p className="text-rose-700">{error}</p>}
      {!error && articles.length === 0 && <p className="text-stone-600">まだ記事がありません。</p>}
      <ul className="divide-y divide-line overflow-hidden rounded-2xl border border-line bg-card">
        {articles.map((article) => (
          <li key={article.id}>
            <Link href={`/articles/${article.id}`} className="grid gap-2 px-5 py-4 hover:bg-paper sm:grid-cols-[1fr_180px_120px_180px] sm:items-center">
              <span className="font-medium">{article.title}</span>
              <span className="text-sm text-stone-600">{article.theme}</span>
              <StatusBadge status={article.status} />
              <span className="text-sm text-stone-500">{formatDate(article.created_at)}</span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
