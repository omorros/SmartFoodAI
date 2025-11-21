const API_BASE = "http://127.0.0.1:8000";

// Send form data to FastAPI to get a shelf-life prediction
export async function predictShelfLife(data) {
  const res = await fetch(`${API_BASE}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!res.ok) throw new Error(`Prediction failed: ${res.status}`);
  return await res.json();
}
