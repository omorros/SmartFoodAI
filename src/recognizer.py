import tensorflow as tf
import numpy as np
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.efficientnet import preprocess_input
from PIL import Image
import io
import os

MODEL_PATH = os.path.join("models", "SmartFoodAI_ImageRecognition_Model.keras")
print(f"[Recognizer] Loading CNN model from: {MODEL_PATH}")

model = tf.keras.models.load_model(MODEL_PATH)
print("[Recognizer] Model loaded successfully!")

CLASS_NAMES = [
    'apple', 'banana', 'bell_pepper_green', 'bell_pepper_red',
    'carrot', 'cucumber', 'grape', 'lemon', 'onion',
    'orange', 'peach', 'potato', 'strawberry', 'tomato'
]

def recognize(image_bytes):
    """
    Takes raw uploaded file bytes (from FastAPI UploadFile)
    and returns prediction.
    """
    try:
        # Load image directly from bytes
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img = img.resize((224, 224))

        img_array = np.array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)

        preds = model.predict(img_array)
        idx = int(np.argmax(preds))
        class_name = CLASS_NAMES[idx]
        confidence = float(np.max(preds))

        return {"class": class_name, "confidence": confidence}

    except Exception as e:
        return {"error": str(e)}
