export type ArticleStatus = "draft" | "processing" | "completed" | "failed";
export type RunStatus = "pending" | "running" | "success" | "failed";

export type ArticleSummary = {
  id: number;
  title: string;
  theme: string;
  status: ArticleStatus;
  created_at: string;
};

export type ArticleDetail = ArticleSummary & {
  keyword: string;
  media: string;
  target_audience: string;
  purpose: string;
  target_length: number;
  tone: string;
  final_content: string | null;
  updated_at: string;
};

export type AgentRun = {
  id: number;
  article_id: number;
  agent_name: string;
  status: RunStatus;
  input_json: Record<string, unknown> | null;
  output_json: Record<string, unknown> | null;
  model: string | null;
  prompt_version: string | null;
  input_tokens: number | null;
  output_tokens: number | null;
  execution_time_ms: number | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
};

export type ArticleVersion = {
  id: number;
  article_id: number;
  version: number;
  content: string;
  created_at: string;
};

export type ArticleInput = {
  theme: string;
  keyword: string;
  media: string;
  target_audience: string;
  purpose: string;
  target_length: number;
  tone: string;
};
