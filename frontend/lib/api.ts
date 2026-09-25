import type { AgentRun, ArticleDetail, ArticleInput, ArticleSummary, ArticleVersion } from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      detail = response.statusText;
    }
    throw new Error(typeof detail === "string" ? detail : "API request failed");
  }
  return response.json() as Promise<T>;
}

export function listArticles() {
  return request<ArticleSummary[]>("/api/articles");
}

export function getArticle(id: number) {
  return request<ArticleDetail>(`/api/articles/${id}`);
}

export function createArticle(input: ArticleInput) {
  return request<{ id: number; status: string }>("/api/articles", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function generateArticle(id: number) {
  return request<{ id: number; status: string }>(`/api/articles/${id}/generate`, { method: "POST" });
}

export function getRuns(id: number) {
  return request<AgentRun[]>(`/api/articles/${id}/runs`);
}

export function retryAgent(id: number, agentName: string) {
  return request<{ id: number; status: string }>(`/api/articles/${id}/agents/${agentName}/retry`, {
    method: "POST",
  });
}

export function getVersions(id: number) {
  return request<ArticleVersion[]>(`/api/articles/${id}/versions`);
}
