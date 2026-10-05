const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function healthCheck(): Promise<{ status: string }> {
  const res = await fetch(`${API_URL}/api/v1/health`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Backend unavailable");
  return res.json();
}
