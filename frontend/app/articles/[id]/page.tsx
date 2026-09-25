"use client";

import { useParams } from "next/navigation";

import { AgentStudio } from "@/components/AgentStudio";

export default function ArticleStatusPage() {
  const params = useParams<{ id: string }>();
  return <AgentStudio articleId={Number(params.id)} />;
}
