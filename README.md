# SmartFood AI  
**An AI-powered food management system to reduce household food waste**

SmartFood AI is a Python-based console application that helps users manage, track, and identify food items intelligently.  
It integrates barcode recognition, image classification, and expiry prediction features to promote sustainable food consumption and reduce waste.

---

## Overview

SmartFood AI allows users to register products manually, by barcode, or through computer vision.  
It stores all items in a local SQLite database, predicts expiry dates for fresh produce, and retrieves product data automatically from the OpenFoodFacts API.

---

## Main Features

### Core Functionality
- Add, edit, view, delete, and consume food items.
- Store data locally using SQLite.
- Track expiry dates with colour-coded urgency indicators:
  - Red = expired  
  - Yellow = expires soon (≤3 days)  
  - Green = fresh (>3 days)

### AI and Machine Learning Components
- **CNN Model:** Identifies fruits and vegetables from images.  
- **Barcode Scanner:** Detects and decodes product barcodes using Pyzxing.  
- **OpenFoodFacts API Integration:** Automatically retrieves product names, brands, and categories by barcode.  
- **Shelf-Life Estimation:** Predicts expiry for products without visible expiry dates.

### User Interaction
- Add items manually, by barcode, or by image recognition.
- File picker interface for selecting barcode images.
- Flexible date input (supports formats like `YYYY-MM-DD` or relative entries such as `3` = three days ago).
- Automatic expiry suggestion based on known shelf-life data.

---

## Technology Stack

| Component | Technology |
|------------|-------------|
| Programming Language | Python 3.12 |
| Database | SQLite |
| Machine Learning | TensorFlow / Keras (CNN) |
| Barcode Recognition | Pyzxing and OpenCV |
| API Integration | OpenFoodFacts REST API |
| Environment | Python Virtual Environment (`.venv`) |
| Interface | Console-based CLI |

---

## Data Source: OpenFoodFacts API

SmartFood AI connects to the [OpenFoodFacts API](https://world.openfoodfacts.org/data) to retrieve:
- Product names, brands, and categories  
- Basic nutritional and packaging information  
- Barcode identifiers (EAN/UPC)

The OpenFoodFacts API includes most major UK and EU supermarket products.  
If a product is not found, the application allows manual data entry.

---

## Future Development

- Voice-based input for natural speech commands.  
- Cloud data synchronisation and multi-device support.  
- Email or app notifications for upcoming expiries.  
- Web dashboard and data visualisation tools.

---

## Author

**Oriol Morros**  
BSc (Hons) Software Engineering — Anglia Ruskin University, Cambridge, UK  
GitHub: [https://github.com/omorros](https://github.com/omorros)

---

## License

This project is released under the **MIT License**.  
You may use, modify, and distribute this software with appropriate attribution.
