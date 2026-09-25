"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { createArticle, generateArticle } from "@/lib/api";

const initial = {
  theme: "AI導入で最初にやるべきこと",
  keyword: "AI 導入",
  media: "note",
  target_audience: "AI初心者の企業担当者",
  purpose: "AIコンサル問い合わせ",
  target_length: 4000,
  tone: "実務的で初心者にもわかりやすい",
};

export default function NewArticlePage() {
  const router = useRouter();
  const [form, setForm] = useState(initial);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  function update(key: keyof typeof form, value: string) {
    setForm((current) => ({
      ...current,
      [key]: key === "target_length" ? Number(value) : value,
    }));
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setPending(true);
    setError(null);
    try {
      const created = await createArticle(form);
      await generateArticle(created.id);
      router.push(`/articles/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "作成に失敗しました");
      setPending(false);
    }
  }

  const fields: { key: keyof typeof form; label: string; multiline?: boolean }[] = [
    { key: "theme", label: "記事テーマ" },
    { key: "keyword", label: "Keyword" },
    { key: "media", label: "Media" },
    { key: "target_audience", label: "Target" },
    { key: "purpose", label: "Purpose" },
    { key: "target_length", label: "Target Length" },
    { key: "tone", label: "Tone", multiline: true },
  ];

  return (
    <div>
      <p className="text-sm text-teal">New article</p>
      <h1 className="mb-8 font-serif text-4xl">新規記事作成</h1>
      <form onSubmit={onSubmit} className="space-y-5 rounded-2xl border border-line bg-card p-6">
        {fields.map((field) => (
          <label key={field.key} className="block">
            <span className="mb-1 block text-sm">{field.label}</span>
            {field.multiline ? (
              <textarea
                required
                value={String(form[field.key])}
                onChange={(event) => update(field.key, event.target.value)}
                className="min-h-24 w-full rounded-xl border border-line bg-paper px-3 py-2"
              />
            ) : (
              <input
                required
                type={field.key === "target_length" ? "number" : "text"}
                min={field.key === "target_length" ? 300 : undefined}
                value={String(form[field.key])}
                onChange={(event) => update(field.key, event.target.value)}
                className="w-full rounded-xl border border-line bg-paper px-3 py-2"
              />
            )}
          </label>
        ))}
        {error && <p className="text-sm text-rose-700">{error}</p>}
        <button disabled={pending} className="rounded-full bg-teal px-5 py-2 text-white disabled:opacity-60">
          {pending ? "開始しています" : "記事作成開始"}
        </button>
      </form>
    </div>
  );
}
