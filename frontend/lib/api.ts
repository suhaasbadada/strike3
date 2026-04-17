const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function apiGet(path: string) {
  const res = await fetch(`${API_URL}${path}`, {
    cache: "no-store",
  });
  return res.json();
}