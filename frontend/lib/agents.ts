import type { AgentRun } from "./types";

export const AGENTS = [
  { name: "persona", label: "Persona Agent", description: "読者像を整理する" },
  { name: "outline", label: "Outline Agent", description: "見出し構成を作る" },
  { name: "writer", label: "Writer Agent", description: "本文を書く" },
  { name: "review", label: "Review Agent", description: "読みやすさとズレを点検する" },
] as const;

export function latestByAgent(runs: AgentRun[]) {
  const map = new Map<string, AgentRun>();
  for (const run of [...runs].sort((a, b) => a.id - b.id)) {
    map.set(run.agent_name, run);
  }
  return map;
}

export function statusLabel(status: string | undefined) {
  switch (status) {
    case "success":
      return "完了";
    case "running":
      return "実行中";
    case "failed":
      return "失敗";
    case "pending":
      return "待機中";
    case "draft":
      return "下書き";
    case "processing":
      return "生成中";
    case "completed":
      return "完成";
    default:
      return "待機中";
  }
}

export function formatDate(value: string) {
  return new Intl.DateTimeFormat("ja-JP", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

export function formatDuration(ms: number | null | undefined) {
  if (ms == null) return "—";
  return `${(ms / 1000).toFixed(1)} 秒`;
}

export function formatTokens(value: number | null | undefined) {
  if (value == null) return "—";
  return value.toLocaleString("ja-JP");
}
