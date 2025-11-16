# ==============================================================
# SMARTFOOD AI - SHELF LIFE PREDICTION API
# ==============================================================
from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import numpy as np
import joblib
import traceback
import os

# ==============================================================
# DEFINE INPUT SCHEMA (for FastAPI request body)
# ==============================================================
class InputData(BaseModel):
    category: str
    location: str
    packaging: str
    state: str
    temperature: float


# ==============================================================
# INITIALIZE FASTAPI APP
# ==============================================================
app = FastAPI(title="SmartFoodAI Shelf-Life Prediction API")

# ==============================================================
# LOAD MODEL ON STARTUP
# ==============================================================
MODEL_PATH = os.path.join("models", "SmartFoodAI_Shelflife_Model.pkl")
model = None

print(f"Looking for model at: {MODEL_PATH}")
try:
    model = joblib.load(MODEL_PATH)
    print(f"Model loaded successfully from {MODEL_PATH}")
except Exception as e:
    print("ERROR while loading model:")
    traceback.print_exc()
    model = None


# ==============================================================
# ROOT ENDPOINT
# ==============================================================
@app.get("/")
def root():
    return {"message": "SmartFoodAI Shelf-Life Prediction API is running!"}


# ==============================================================
# PREDICTION ENDPOINT
# ==============================================================
@app.post("/predict")
async def predict(input_data: InputData):
    try:
        if model is None:
            return {"error": "Model not loaded"}

        # Prepare input for prediction
        data = {
            "category": [input_data.category.lower()],
            "location": [input_data.location.lower()],
            "packaging": [input_data.packaging.lower()],
            "state": [input_data.state.lower()],
            "temperature": [input_data.temperature],
        }

        df = pd.DataFrame(data)
        print("\nIncoming data:\n", df)

        # Predict log ratio (as trained)
        ratio_log_pred = model.predict(df)[0]

        # Reverse the log transform and calibrate
        ratio = max(0.3, min(3.0, float(np.exp(ratio_log_pred) + 0.7)))

        # Use baseline realistic reference values
        baseline_rules = {
            "fruit": {"fridge": 7, "freezer": 180, "pantry": 3},
            "meat": {"fridge": 5, "freezer": 270, "pantry": 0.5},
            "snack": {"fridge": 60, "freezer": 120, "pantry": 180},
            "vegetable": {"fridge": 10, "freezer": 180, "pantry": 4},
            "dairy": {"fridge": 14, "freezer": 90, "pantry": 2},
            "grain": {"fridge": 60, "freezer": 180, "pantry": 365},
            "beverage": {"fridge": 120, "freezer": 180, "pantry": 180},
            "unknown": {"fridge": 10, "freezer": 60, "pantry": 30},
        }

        baseline = baseline_rules.get(input_data.category.lower(), baseline_rules["unknown"]).get(
            input_data.location.lower(), 7
        )

        predicted_days = round(baseline * ratio, 1)
        predicted_days = max(predicted_days, 0.1)  # Avoid negative or zero days

        return {
            "predicted_shelf_life_days": predicted_days,
            "baseline_days": baseline,
            "calibrated_ratio": ratio,
            "input_data": data,
            "status": "success"
        }

    except Exception as e:
        print("ERROR in /predict:", e)
        traceback.print_exc()
        return {"error": str(e)}



# ==============================================================
# RUN (for local debugging)
# ==============================================================
# Run manually with:
# uvicorn src.api_server:app --reload
# Then open: http://127.0.0.1:8000/docs
