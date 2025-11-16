# ==============================================================
# api_server.py — SmartFoodAI FastAPI backend
# ==============================================================

from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import pandas as pd
import os

# --------------------------------------------------------------
# Initialize FastAPI app
# --------------------------------------------------------------
app = FastAPI(title="SmartFoodAI Shelf Life Prediction API")

# --------------------------------------------------------------
# Load model and preprocessing assets
# --------------------------------------------------------------
MODEL_PATH = os.path.join("models", "shelf_life_model.pkl")
SCALER_PATH = os.path.join("models", "scaler.pkl")
COLUMNS_PATH = os.path.join("models", "model_columns.pkl")

model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)
model_columns = joblib.load(COLUMNS_PATH)

# --------------------------------------------------------------
# Define expected input format
# --------------------------------------------------------------
class ProductInput(BaseModel):
    category: str
    location: str
    packaging: str
    state: str

# --------------------------------------------------------------
# Root endpoint
# --------------------------------------------------------------
@app.get("/")
def home():
    return {"message": "SmartFoodAI Shelf Life Prediction API is running."}

# --------------------------------------------------------------
# Prediction endpoint
# --------------------------------------------------------------
@app.post("/predict")
def predict(data: ProductInput):
    # Convert input to DataFrame
    df = pd.DataFrame([data.dict()])

    # One-hot encode and align columns
    df_encoded = pd.get_dummies(df)
    for col in model_columns:
        if col not in df_encoded:
            df_encoded[col] = 0
    df_encoded = df_encoded[model_columns]

    # Scale numeric columns
    df_scaled = scaler.transform(df_encoded)

    # Predict
    prediction = model.predict(df_scaled)[0]

    return {
        "category": data.category,
        "location": data.location,
        "predicted_shelf_life_days": round(float(prediction), 2)
    }
