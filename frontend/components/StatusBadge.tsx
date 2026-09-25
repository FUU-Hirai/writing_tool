import { statusLabel } from "@/lib/agents";

const tones: Record<string, string> = {
  draft: "bg-stone-200 text-stone-700",
  processing: "bg-amber-100 text-amber-800",
  running: "bg-amber-100 text-amber-800",
  completed: "bg-teal/10 text-teal",
  success: "bg-teal/10 text-teal",
  failed: "bg-rose-100 text-rose-800",
  pending: "bg-stone-100 text-stone-500",
};

export function StatusBadge({ status }: { status?: string }) {
  const key = status ?? "pending";
  return (
    <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${tones[key] ?? tones.pending}`}>
      {statusLabel(status)}
    </span>
  );
}
