import React, { useState } from "react";
import { predictShelfLife } from "../api/api";

export default function AddItemForm() {
  const [result, setResult] = useState(null);

  const handleTest = async () => {
    const payload = {
      category: "meat",
      location: "fridge",
      packaging: "sealed",
      state: "raw",
      temperature: 4,
    };

    try {
      const res = await predictShelfLife(payload);
      setResult(res);
    } catch (err) {
      console.error("Error:", err);
      setResult({ error: "API connection failed. Make sure FastAPI is running." });
    }
  };

  return (
    <div style={{ padding: "2rem" }}>
      <h2>Test SmartFoodAI API Connection</h2>
      <button onClick={handleTest}>Run Prediction Test</button>

      {result && (
        <div style={{ marginTop: "2rem", background: "#f4f4f4", padding: "1rem" }}>
          <h3>API Response:</h3>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
