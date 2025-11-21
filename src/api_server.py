import sys, os

# FORCE correct module root manually
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_PATH = os.path.abspath(os.path.dirname(__file__))

sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, SRC_PATH)

print("\n[FIXED PATHS]")
print("Added to sys.path:", PROJECT_ROOT)
print("Added to sys.path:", SRC_PATH)
print()

import recognizer
print(">>> RECOGNIZER MODULE LOADED FROM:", recognizer.__file__)


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
# SMARTFOOD AI - IMAGE RECOGNITION MODULE (EfficientNetB0)
# ==============================================================
from fastapi import UploadFile, File
from recognizer import recognize
import shutil, uuid


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
# ==============================================================
# INITIALIZE FASTAPI APP
# ==============================================================
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="SmartFoodAI Shelf-Life Prediction API")

# --- Enable CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # You can restrict later to ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
# IMAGE RECOGNITION ENDPOINT (EfficientNetB0)
# ==============================================================

from fastapi import UploadFile, File

@app.post("/predict-image")
async def predict_image(file: UploadFile = File(...)):
    try:
        # Read file bytes
        contents = await file.read()

        # Pass to recognizer
        result = recognize(contents)

        return {"result": result}

    except Exception as e:
        return {"error": str(e)}

# ==============================================================
# ADD ITEM ENDPOINT (used by React frontend)
# ==============================================================
from fastapi import Request
from db_manager import add_item, init_db

@app.post("/add_item")
async def add_item_endpoint(request: Request):
    """
    Accepts JSON from frontend and saves item into SQLite database.
    Expected fields:
      name, category, qty, unit, location, purchased_on, expiry_on, source, notes
    """
    try:
        data = await request.json()
        print("Incoming add_item data:", data)

        init_db()  # Ensure table exists

        name = data.get("name")
        category = data.get("category", "")
        qty = float(data.get("qty", 1))
        unit = data.get("unit", "")
        location = data.get("location", "Fridge")
        purchased_on = data.get("purchased_on")
        expiry_on = data.get("expiry_on")
        source = data.get("source", "WebApp")
        notes = data.get("notes", "")

        iid = add_item(name, category, qty, unit, location, purchased_on, expiry_on, source, notes)

        return {"status": "success", "id": iid, "message": f"Item '{name}' added successfully."}

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

# ==============================================================
# RUN (for local debugging)
# ==============================================================
# Run manually with:
# uvicorn src.api_server:app --reload
# Then open: http://127.0.0.1:8000/docs
