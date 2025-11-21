import React, { useState } from "react";
import { predictShelfLife } from "../api/api";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import { DatePicker } from "@mui/x-date-pickers/DatePicker";
import dayjs from "dayjs";

const API_BASE = "http://127.0.0.1:8000";

export default function AddItemInteractive() {
  const [step, setStep] = useState("name");
  const [form, setForm] = useState({
    name: "",
    category: "",
    location: "",
    packaging: "sealed",
    state: "raw",
  });
  const [prediction, setPrediction] = useState(null);
  const [expiryDate, setExpiryDate] = useState(null);
  const [customExpiry, setCustomExpiry] = useState(dayjs());
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(false);

  const next = (nextStep) => setStep(nextStep);

  const autoDetectCategory = (foodName) => {
    const lower = foodName.toLowerCase();
    if (lower.includes("apple") || lower.includes("banana")) return "fruit";
    if (lower.includes("chicken") || lower.includes("beef")) return "meat";
    if (lower.includes("milk")) return "dairy";
    if (lower.includes("bread") || lower.includes("rice")) return "grain";
    return "unknown";
  };

  const handleNameSubmit = (e) => {
    e.preventDefault();
    const detected = autoDetectCategory(form.name);
    setForm({ ...form, category: detected });
    next("categoryConfirm");
  };

  const handleCategoryConfirm = (confirm) => {
    if (confirm) next("location");
    else next("categoryManual");
  };

  const handlePredict = async () => {
    setLoading(true);
    const payload = {
      category: form.category,
      location: form.location,
      packaging: form.packaging,
      state: form.state,
      temperature:
        form.location === "Fridge"
          ? 4
          : form.location === "Freezer"
          ? -18
          : 20,
    };

    try {
      const res = await predictShelfLife(payload);
      setPrediction(res);

      // Calculate default predicted expiry date
      const predictedDays = res.predicted_shelf_life_days || 0;
      const predictedDate = dayjs().add(predictedDays, "day");
      setExpiryDate(predictedDate);
      next("done");
    } catch (err) {
      console.error("Prediction failed:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (useCustom = false) => {
    const chosenDate = useCustom ? customExpiry : expiryDate;
    if (!chosenDate) return;

    const item = {
      name: form.name,
      category: form.category,
      qty: 1,
      unit: "pcs",
      location: form.location,
      purchased_on: new Date().toISOString().split("T")[0],
      expiry_on: chosenDate.format("YYYY-MM-DD"),
      source: "WebApp",
      notes: useCustom
        ? "Custom expiry date selected by user."
        : `Predicted shelf life: ${prediction?.predicted_shelf_life_days} days`,
    };

    try {
      const res = await fetch(`${API_BASE}/add_item`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(item),
      });
      if (res.ok) setSaved(true);
    } catch (err) {
      console.error("Error saving item:", err);
    }
  };

  return (
    <div style={{ padding: "2rem", maxWidth: 600 }}>
      <h2>Add Item (Interactive)</h2>

      {step === "name" && (
        <form onSubmit={handleNameSubmit}>
          <label>
            What’s the food name? <br />
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              required
            />
          </label>
          <button type="submit" style={{ marginTop: "1rem" }}>
            Continue →
          </button>
        </form>
      )}

      {step === "categoryConfirm" && (
        <div>
          <p>
            Detected category: <b>{form.category}</b>. Is this correct?
          </p>
          <button onClick={() => handleCategoryConfirm(true)}>Yes</button>
          <button onClick={() => handleCategoryConfirm(false)}>No</button>
        </div>
      )}

      {step === "categoryManual" && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            next("location");
          }}
        >
          <label>
            Enter correct category:
            <input
              type="text"
              value={form.category}
              onChange={(e) => setForm({ ...form, category: e.target.value })}
            />
          </label>
          <button type="submit" style={{ marginTop: "1rem" }}>
            Continue →
          </button>
        </form>
      )}

      {step === "location" && (
        <div>
          <p>Where is it stored?</p>
          {["Fridge", "Freezer", "Pantry"].map((loc) => (
            <button
              key={loc}
              onClick={() => {
                setForm({ ...form, location: loc });
                next("packaging");
              }}
              style={{ marginRight: "0.5rem" }}
            >
              {loc}
            </button>
          ))}
        </div>
      )}

      {step === "packaging" && (
        <div>
          <p>Is it sealed or open?</p>
          {["sealed", "open"].map((pkg) => (
            <button
              key={pkg}
              onClick={() => {
                setForm({ ...form, packaging: pkg });
                next("state");
              }}
              style={{ marginRight: "0.5rem" }}
            >
              {pkg}
            </button>
          ))}
        </div>
      )}

      {step === "state" && (
        <div>
          <p>Is it raw or cooked?</p>
          {["raw", "cooked"].map((s) => (
            <button
              key={s}
              onClick={() => {
                setForm({ ...form, state: s });
                handlePredict();
              }}
              style={{ marginRight: "0.5rem" }}
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {loading && (
        <p style={{ marginTop: "2rem", color: "#555" }}>
          Predicting shelf life... please wait
        </p>
      )}

      {step === "done" && prediction && (
        <div
          style={{
            marginTop: "2rem",
            background: "#f8f9fa",
            borderRadius: "8px",
            padding: "1.5rem",
            boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
          }}
        >
          <h3>Prediction Summary</h3>
          <p><b>Item:</b> {form.name}</p>
          <p><b>Category:</b> {form.category}</p>
          <p><b>Location:</b> {form.location}</p>
          <p><b>Packaging:</b> {form.packaging}</p>
          <p><b>State:</b> {form.state}</p>
          <p>
            <b>Expected Shelf Life:</b>{" "}
            {prediction.predicted_shelf_life_days.toFixed(1)} days
          </p>

          <LocalizationProvider dateAdapter={AdapterDayjs}>
            <DatePicker
              label="Select custom expiry date"
              value={customExpiry}
              onChange={(newValue) => setCustomExpiry(newValue)}
              slotProps={{ textField: { fullWidth: true } }}
            />
          </LocalizationProvider>

          <div style={{ marginTop: "1rem" }}>
            <button
              onClick={() => handleSave(false)}
              style={{ marginRight: "1rem" }}
            >
              Use Predicted Date
            </button>
            <button onClick={() => handleSave(true)}>Use Custom Date</button>
          </div>

          {saved && (
            <p style={{ color: "green", marginTop: "1rem" }}>
              Saved successfully to inventory.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
