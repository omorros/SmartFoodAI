const API_BASE = "http://127.0.0.1:8000";

// Predict shelf life from FastAPI
export async function predictShelfLife(data) {
  const res = await fetch(`${API_BASE}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!res.ok) throw new Error(`Prediction failed: ${res.status}`);
  return await res.json();
}

// Save item to inventory
export async function saveItem(item) {
  const res = await fetch(`${API_BASE}/add_item`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(item),
  });

  if (!res.ok) throw new Error(`Saving item failed: ${res.status}`);
  return await res.json();
}
