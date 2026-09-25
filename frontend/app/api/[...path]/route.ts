const METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"] as const;

async function proxy(request: Request, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const base = process.env.INTERNAL_API_URL || "http://localhost:8000";
  const incoming = new URL(request.url);
  const target = `${base}/api/${path.join("/")}${incoming.search}`;
  try {
    const response = await fetch(target, {
      method: request.method,
      headers: { "Content-Type": request.headers.get("content-type") || "application/json" },
      body: request.method === "GET" || request.method === "HEAD" ? undefined : await request.text(),
      cache: "no-store",
    });
    const text = await response.text();
    return new Response(text, {
      status: response.status,
      headers: { "Content-Type": response.headers.get("content-type") || "application/json" },
    });
  } catch {
    return Response.json({ detail: "backend is unavailable" }, { status: 502 });
  }
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;

void METHODS;
