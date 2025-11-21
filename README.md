# SmartFoodAI
An AI-powered food management, expiry-tracking, and image-recognition system with both a console interface and a React-based web frontend.

SmartFoodAI combines computer vision, barcode scanning, expiry prediction, a FastAPI backend, and a React frontend to help reduce household food waste.  
Users can register products manually, via barcode, or through image recognition using a custom-trained CNN model.

The project includes:
- A console-based CLI
- A backend API (FastAPI)
- A React web interface under `/frontend`

## Key Features

### 1. Food Inventory Management
- Add, update, delete, and consume food items.
- SQLite-based storage.
- Colour-coded expiry indicators:
  - Red: expired
  - Yellow: expiring soon (≤ 3 days)
  - Green: fresh

### 2. Computer Vision (Image Recognition)
- TensorFlow/Keras CNN model.
- Image classification via FastAPI (`/predict` endpoint).
- User confirmation step after prediction.

### 3. Barcode Scanning
- Barcode extraction via Pyzxing and OpenCV.
- Automatic product lookup using the OpenFoodFacts API.

### 4. Expiry Prediction Engine
- Shelf-life rules for fruits and vegetables.
- Automatic expiry suggestions for items without visible dates.

### 5. User Interfaces
**Console Application:**  
- Full text-based menu system

**Web Interface (React, located in `/frontend`):**  
- Modern UI for interacting with the FastAPI backend  
- Product viewing and future real-time inventory features  

## Project Structure

SmartFoodAI/
│
├── frontend/                       # React web interface
│   ├── src/
│   ├── public/
│   └── package.json
│
├── models/
│   ├── fruit_veg_model.h5
│   └── label_map.json
│
├── recognizer/
│   ├── recognizer.py
│   ├── preprocess.py
│   └── fastapi_app.py              # FastAPI inference server
│
├── barcode/
│   └── barcode_reader.py
│
├── database/
│   └── smartfood.db
│
├── db_manager.py
├── utils.py
├── main.py                         # Console menu
├── requirements.txt
└── README.md

## Technology Stack

### Backend
- Python 3.12  
- FastAPI  
- SQLite  
- TensorFlow / Keras  
  - CNN image-classification model for fruit and vegetable recognition  
  - Regression-based expiry prediction model for estimating shelf-life  
- Pyzxing and OpenCV for barcode detection  
- OpenFoodFacts REST API for product metadata  

### Frontend
- React  
- JavaScript / TypeScript (depending on project setup)  
- Vite development server  

### Interfaces
- Console-based CLI  
- Web UI (React frontend communicating with the FastAPI backend)

## Machine Learning Models

SmartFoodAI integrates two separate machine learning components that together enable automated food recognition and expiry estimation.

### 1. Image Classification Model (CNN)

**Purpose:**  
Identify fruits and vegetables from user images.

**Architecture:**  
- TensorFlow / Keras Sequential CNN  
- Convolutional layers with ReLU activation  
- Max-pooling layers for spatial reduction  
- Fully connected dense layers  
- Softmax output for multi-class classification

**Input Pipeline:**  
- Images resized to 128×128  
- Normalised pixel values (0–1)  
- Augmentation applied during training (rotation, flip, zoom)

**Model Outputs:**  
- Predicted class label  
- Classification confidence  
- Used by the backend to suggest product names when adding new items

**Files:**  
- `models/fruit_veg_model.h5`  
- `models/label_map.json`

---

### 2. Expiry Prediction Model (Regression-Based)

**Purpose:**  
Predict the estimated expiry date of products that do not contain a visible expiry label (e.g., fresh produce).

**Method:**  
A rule-based regression model that combines:
- Known shelf-life datasets  
- Product category mappings  
- Date-of-purchase estimation  
- User-defined overrides

The model outputs:
- Estimated expiry date  
- Confidence factor (based on category stability)
- Colour-coded freshness indicators

This module is implemented inside:
- `utils.py` (shelf-life database + heuristics)
- `db_manager.py` (integration when storing items)

---

### 3. API Integration for Model Inference

The `recognizer/fastapi_app.py` provides:
- `/predict` endpoint for CNN inference  
- `/health` endpoint for readiness checks

The React frontend communicates with this API to:
- Upload an image  
- Receive classification  
- Allow the user to confirm or correct before inserting into the database

---

### 4. Planned Future ML Enhancements
- Transformer-based model for multi-class food recognition  
- OCR-based expiry extraction from package labels  
- Personalised expiry estimation using historical user data  
- Cloud-hosted model for real-time web inference
